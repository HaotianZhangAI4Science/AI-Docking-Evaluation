# Copyright 2021 AlQuraishi Laboratory
# Copyright 2021 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations
from typing import Tuple, Any, Sequence, Callable

import numpy as np
import torch
from torch.nn import functional as F


def rot_matmul(
    a: torch.Tensor,
    b: torch.Tensor
) -> torch.Tensor:
    """
        Performs matrix multiplication of two rotation matrix tensors. Written
        out by hand to avoid transfer to low-precision tensor cores.

        Args:
            a: [*, 3, 3] left multiplicand
            b: [*, 3, 3] right multiplicand
        Returns:
            The product ab
    """
    row_1 = torch.stack(
        [
            a[..., 0, 0] * b[..., 0, 0]
            + a[..., 0, 1] * b[..., 1, 0]
            + a[..., 0, 2] * b[..., 2, 0],
            a[..., 0, 0] * b[..., 0, 1]
            + a[..., 0, 1] * b[..., 1, 1]
            + a[..., 0, 2] * b[..., 2, 1],
            a[..., 0, 0] * b[..., 0, 2]
            + a[..., 0, 1] * b[..., 1, 2]
            + a[..., 0, 2] * b[..., 2, 2],
        ],
        dim=-1,
    )
    row_2 = torch.stack(
        [
            a[..., 1, 0] * b[..., 0, 0]
            + a[..., 1, 1] * b[..., 1, 0]
            + a[..., 1, 2] * b[..., 2, 0],
            a[..., 1, 0] * b[..., 0, 1]
            + a[..., 1, 1] * b[..., 1, 1]
            + a[..., 1, 2] * b[..., 2, 1],
            a[..., 1, 0] * b[..., 0, 2]
            + a[..., 1, 1] * b[..., 1, 2]
            + a[..., 1, 2] * b[..., 2, 2],
        ],
        dim=-1,
    )
    row_3 = torch.stack(
        [
            a[..., 2, 0] * b[..., 0, 0]
            + a[..., 2, 1] * b[..., 1, 0]
            + a[..., 2, 2] * b[..., 2, 0],
            a[..., 2, 0] * b[..., 0, 1]
            + a[..., 2, 1] * b[..., 1, 1]
            + a[..., 2, 2] * b[..., 2, 1],
            a[..., 2, 0] * b[..., 0, 2]
            + a[..., 2, 1] * b[..., 1, 2]
            + a[..., 2, 2] * b[..., 2, 2],
        ],
        dim=-1,
    )

    return torch.stack([row_1, row_2, row_3], dim=-2)


def rot_vec_mul(
    r: torch.Tensor,
    t: torch.Tensor
) -> torch.Tensor:
    """
        Applies a rotation to a vector. Written out by hand to avoid transfer
        to low-precision tensor cores.

        Args:
            r: [*, 3, 3] rotation matrices
            t: [*, 3] coordinate tensors
        Returns:
            [*, 3] rotated coordinates
    """
    x = t[..., 0]
    y = t[..., 1]
    z = t[..., 2]
    return torch.stack(
        [
            r[..., 0, 0] * x + r[..., 0, 1] * y + r[..., 0, 2] * z,
            r[..., 1, 0] * x + r[..., 1, 1] * y + r[..., 1, 2] * z,
            r[..., 2, 0] * x + r[..., 2, 1] * y + r[..., 2, 2] * z,
        ],
        dim=-1,
    )


class T:
    """
        A class representing an affine transformation. Essentially a wrapper
        around two torch tensors: a [*, 3, 3] rotation and a [*, 3]
        translation. Designed to behave approximately like a single torch
        tensor with the shape of the shared dimensions of its component parts.
    """
    def __init__(self,
        rots: torch.Tensor,
        trans: torch.Tensor
    ):
        """
            Args:
                rots: A [*, 3, 3] rotation tensor
                trans: A corresponding [*, 3] translation tensor
        """
        self.rots = rots
        self.trans = trans

        if self.rots is None and self.trans is None:
            raise ValueError("Only one of rots and trans can be None")
        elif self.rots is None:
            self.rots = T._identity_rot(
                self.trans.shape[:-1],
                self.trans.dtype,
                self.trans.device,
                self.trans.requires_grad,
            )
        elif self.trans is None:
            self.trans = T._identity_trans(
                self.rots.shape[:-2],
                self.rots.dtype,
                self.rots.device,
                self.rots.requires_grad,
            )

        if (
            self.rots.shape[-2:] != (3, 3)
            or self.trans.shape[-1] != 3
            or self.rots.shape[:-2] != self.trans.shape[:-1]
        ):
            raise ValueError("Incorrectly shaped input")

    def __getitem__(self,
        index: Any,
    ) -> T:
        """
            Indexes the affine transformation with PyTorch-style indices.
            The index is applied to the shared dimensions of both the rotation
            and the translation.

            E.g.::

                t = T(torch.rand(10, 10, 3, 3), torch.rand(10, 10, 3))
                indexed = t[3, 4:6]
                assert(indexed.shape == (2,))
                assert(indexed.rots.shape == (2, 3, 3))
                assert(indexed.trans.shape == (2, 3))

            Args:
                index: A standard torch tensor index. E.g. 8, (10, None, 3),
                or (3, slice(0, 1, None))
            Returns:
                The indexed tensor
        """
        if type(index) != tuple:
            index = (index,)
        return T(
            self.rots[index + (slice(None), slice(None))],
            self.trans[index + (slice(None),)],
        )

    def __eq__(self,
        obj: T,
    ) -> bool:
        """
            Compares two affine transformations. Returns true iff the
            transformations are pointwise identical. Does not account for
            floating point imprecision.
        """
        return bool(
            torch.all(self.rots == obj.rots) and
            torch.all(self.trans == obj.trans)
        )

    def __mul__(self,
        right: torch.Tensor,
    ) -> T:
        """
            Pointwise right multiplication of the affine transformation with a
            tensor. Multiplication is broadcast over the rotation/translation
            dimensions.

            Args:
                right: The right multiplicand
            Returns:
                The product transformation
        """
        rots = self.rots * right[..., None, None]
        trans = self.trans * right[..., None]

        return T(rots, trans)

    def __rmul__(self,
        left: torch.Tensor,
    ) -> T:
        """
            Pointwise left multiplication of the affine transformation with a
            tensor. Multiplication is broadcast over the rotation/translation
            dimensions.

            Args:
                left: The left multiplicand
            Returns:
                The product transformation
        """
        return self.__mul__(left)

    @property
    def shape(self) -> torch.Size:
        """
            Returns the shape of the shared dimensions of the rotation and
            the translation.

            Returns:
                The shape of the transformation
        """
        s = self.rots.shape[:-2]
        return s if len(s) > 0 else torch.Size([1])

    def get_rots(self):
        """
            Getter for the rotation.

            Returns:
                The stored rotation.
        """
        return self.rots

    def get_trans(self) -> torch.Tensor:
        """
            Getter for the translation.

            Returns:
                The stored translation.
        """
        return self.trans

    def compose(self,
        t: T,
    ) -> T:
        """
            Composes the transformation with another.

            Args:
                t: The inner transformation.
            Returns:
                The composed transformation.
        """
        rot_1, trn_1 = self.rots, self.trans
        rot_2, trn_2 = t.rots, t.trans

        rot = rot_matmul(rot_1, rot_2)
        trn = rot_vec_mul(rot_1, trn_2) + trn_1

        return T(rot, trn)

    def add(self,
        t: T,
    ) -> T:
        """
            Composes the transformation with another.

            Args:
                t: The inner transformation.
            Returns:
                The composed transformation.
        """
        rot_1, trn_1 = self.rots, self.trans
        rot_2, trn_2 = t.rots, t.trans

        rot = rot_matmul(rot_1, rot_2)
        trn = trn_2 + trn_1

        return T(rot, trn)

    def apply(self,
        pts: torch.Tensor,
    ) -> torch.Tensor:
        """
            Applies the transformation to a coordinate tensor.

            Args:
                pts: A [*, 3] coordinate tensor.
            Returns:
                The transformed points.
        """
        r, t = self.rots, self.trans
        rotated = rot_vec_mul(r, pts)
        return rotated + t

    def invert_apply(self,
        pts: torch.Tensor
    ) -> torch.Tensor:
        """
            Applies the inverse of the transformation to a coordinate tensor.

            Args:
                pts: A [*, 3] coordinate tensor
            Returns:
                The transformed points.
        """
        r, t = self.rots, self.trans
        pts = pts - t
        return rot_vec_mul(r.transpose(-1, -2), pts)

    def invert(self) -> T:
        """
            Inverts the transformation.

            Returns:
                The inverse transformation.
        """
        rot_inv = self.rots.transpose(-1, -2)
        trn_inv = rot_vec_mul(rot_inv, self.trans)

        return T(rot_inv, -1 * trn_inv)

    def unsqueeze(self,
        dim: int,
    ) -> T:
        """
            Analogous to torch.unsqueeze. The dimension is relative to the
            shared dimensions of the rotation/translation.

            Args:
                dim: A positive or negative dimension index.
            Returns:
                The unsqueezed transformation.
        """
        if dim >= len(self.shape):
            raise ValueError("Invalid dimension")
        rots = self.rots.unsqueeze(dim if dim >= 0 else dim - 2)
        trans = self.trans.unsqueeze(dim if dim >= 0 else dim - 1)

        return T(rots, trans)

    @staticmethod
    def _identity_rot(
        shape: Tuple[int],
        dtype: torch.dtype,
        device: torch.device,
        requires_grad: bool,
    ) -> torch.Tensor:
        rots = torch.eye(
            3, dtype=dtype, device=device, requires_grad=requires_grad
        )
        rots = rots.view(*((1,) * len(shape)), 3, 3)
        rots = rots.expand(*shape, -1, -1)

        return rots

    @staticmethod
    def _identity_trans(
        shape: Tuple[int],
        dtype: torch.dtype,
        device: torch.device,
        requires_grad: bool
    ) -> torch.Tensor:
        trans = torch.zeros(
            (*shape, 3), dtype=dtype, device=device, requires_grad=requires_grad
        )
        return trans

    @staticmethod
    def identity(
        shape: Tuple[int],
        dtype: torch.dtype,
        device: torch.device,
        requires_grad: bool = True
    ) -> T:
        """
            Constructs an identity transformation.

            Args:
                shape:
                    The desired shape
                dtype:
                    The dtype of both internal tensors
                device:
                    The device of both internal tensors
                requires_grad:
                    Whether grad should be enabled for the internal tensors
            Returns:
                The identity transformation
        """
        return T(
            T._identity_rot(shape, dtype, device, requires_grad),
            T._identity_trans(shape, dtype, device, requires_grad),
        )

    @staticmethod
    def from_4x4(
        t: torch.Tensor
    ) -> T:
        """
            Constructs a transformation from a homogenous transformation
            tensor.

            Args:
                t: [*, 4, 4] homogenous transformation tensor
            Returns:
                T object with shape [*]
        """
        rots = t[..., :3, :3]
        trans = t[..., :3, 3]
        return T(rots, trans)

    def to_4x4(self) -> torch.Tensor:
        """
            Converts a transformation to a homogenous transformation tensor.

            Returns:
                A [*, 4, 4] homogenous transformation tensor
        """
        tensor = self.rots.new_zeros((*self.shape, 4, 4))
        tensor[..., :3, :3] = self.rots
        tensor[..., :3, 3] = self.trans
        tensor[..., 3, 3] = 1
        return tensor

    @staticmethod
    def from_tensor(t: torch.Tensor) -> T:
        """
            Constructs a transformation from a homogenous transformation
            tensor.

            Args:
                t: A [*, 4, 4] homogenous transformation tensor
            Returns:
                A transformation object with shape [*]
        """
        return T.from_4x4(t)

    @staticmethod
    def from_3_points(
        p_neg_x_axis: torch.Tensor,
        origin: torch.Tensor,
        p_xy_plane: torch.Tensor,
        eps: float = 1e-8
    ) -> T:
        """
            Implements algorithm 21. Constructs transformations from sets of 3
            points using the Gram-Schmidt algorithm.

            Args:
                p_neg_x_axis: [*, 3] coordinates
                origin: [*, 3] coordinates used as frame origins
                p_xy_plane: [*, 3] coordinates
                eps: Small epsilon value
            Returns:
                A transformation object of shape [*]
        """
        p_neg_x_axis = torch.unbind(p_neg_x_axis, dim=-1)
        origin = torch.unbind(origin, dim=-1)
        p_xy_plane = torch.unbind(p_xy_plane, dim=-1)

        e0 = [c1 - c2 for c1, c2 in zip(origin, p_neg_x_axis)]
        e1 = [c1 - c2 for c1, c2 in zip(p_xy_plane, origin)]

        denom = torch.sqrt(sum((c * c for c in e0)) + eps)
        e0 = [c / denom for c in e0]
        dot = sum((c1 * c2 for c1, c2 in zip(e0, e1)))
        e1 = [c2 - c1 * dot for c1, c2 in zip(e0, e1)]
        denom = torch.sqrt(sum((c * c for c in e1)) + eps)
        e1 = [c / denom for c in e1]
        e2 = [
            e0[1] * e1[2] - e0[2] * e1[1],
            e0[2] * e1[0] - e0[0] * e1[2],
            e0[0] * e1[1] - e0[1] * e1[0],
        ]

        rots = torch.stack([c for tup in zip(e0, e1, e2) for c in tup], dim=-1)
        rots = rots.reshape(rots.shape[:-1] + (3, 3))

        return T(rots, torch.stack(origin, dim=-1))

    @staticmethod
    def concat(
        ts: Sequence[T],
        dim: int,
    ) -> T:
        """
            Concatenates transformations along a new dimension.

            Args:
                ts:
                    A list of T objects
                dim:
                    The dimension along which the transformations should be
                    concatenated
            Returns:
                A concatenated transformation object
        """
        rots = torch.cat([t.rots for t in ts], dim=dim if dim >= 0 else dim - 2)
        trans = torch.cat(
            [t.trans for t in ts], dim=dim if dim >= 0 else dim - 1
        )

        return T(rots, trans)

    def map_tensor_fn(self, fn: Callable[[torch.Tensor], torch.Tensor]) -> T:
        """
            Apply a function that takes a tensor as its only argument to the
            rotations and translations, treating the final two/one
            dimension(s), respectively, as batch dimensions.

            E.g.: Given t, an instance of T of shape [N, M], this function can
            be used to sum out the second dimension thereof as follows::

                t = t.map_tensor_fn(lambda x: torch.sum(x, dim=-1))

            The resulting object has rotations of shape [N, 3, 3] and
            translations of shape [N, 3]

            Args:
                fn: A function that takes only a tensor as its argument
            Returns:
                The transformed transformation object.
        """
        rots = self.rots.view(*self.rots.shape[:-2], 9)
        rots = torch.stack(list(map(fn, torch.unbind(rots, -1))), dim=-1)
        rots = rots.view(*rots.shape[:-1], 3, 3)

        trans = torch.stack(list(map(fn, torch.unbind(self.trans, -1))), dim=-1)

        return T(rots, trans)

    def stop_rot_gradient(self) -> T:
        """
            Detaches the contained rotation tensor.

            Returns:
                A version of the transformation with detached rotations
        """
        return T(self.rots.detach(), self.trans)

    def scale_translation(self, factor: int) -> T:
        """
            Scales the contained translation tensor by a constant factor.

            Returns:
                A version of the transformation with scaled translations
        """
        return T(self.rots, self.trans * factor)

    @staticmethod
    def make_transform_from_reference(n_xyz, ca_xyz, c_xyz, eps=1e-20):
        """
            Returns a transformation object from reference coordinates.

            Note that this method does not take care of symmetries. If you
            provide the atom positions in the non-standard way, the N atom will
            end up not at [-0.527250, 1.359329, 0.0] but instead at
            [-0.527250, -1.359329, 0.0]. You need to take care of such cases in
            your code.

            Args:
                n_xyz: A [*, 3] tensor of nitrogen xyz coordinates.
                ca_xyz: A [*, 3] tensor of carbon alpha xyz coordinates.
                c_xyz: A [*, 3] tensor of carbon xyz coordinates.
            Returns:
                A transformation object. After applying the translation and
                rotation to the reference backbone, the coordinates will
                approximately equal to the input coordinates.
        """
        translation = -1 * ca_xyz
        n_xyz = n_xyz + translation
        c_xyz = c_xyz + translation

        c_x, c_y, c_z = [c_xyz[..., i] for i in range(3)]
        norm = torch.sqrt(eps + c_x ** 2 + c_y ** 2)
        sin_c1 = -c_y / norm
        cos_c1 = c_x / norm
        zeros = sin_c1.new_zeros(sin_c1.shape)
        ones = sin_c1.new_ones(sin_c1.shape)

        c1_rots = sin_c1.new_zeros((*sin_c1.shape, 3, 3))
        c1_rots[..., 0, 0] = cos_c1
        c1_rots[..., 0, 1] = -1 * sin_c1
        c1_rots[..., 1, 0] = sin_c1
        c1_rots[..., 1, 1] = cos_c1
        c1_rots[..., 2, 2] = 1

        norm = torch.sqrt(eps + c_x ** 2 + c_y ** 2 + c_z ** 2)
        sin_c2 = c_z / norm
        cos_c2 = torch.sqrt(c_x ** 2 + c_y ** 2) / norm

        c2_rots = sin_c2.new_zeros((*sin_c2.shape, 3, 3))
        c2_rots[..., 0, 0] = cos_c2
        c2_rots[..., 0, 2] = sin_c2
        c2_rots[..., 1, 1] = 1
        c1_rots[..., 2, 0] = -1 * sin_c2
        c1_rots[..., 2, 2] = cos_c2

        c_rots = rot_matmul(c2_rots, c1_rots)
        n_xyz = rot_vec_mul(c_rots, n_xyz)

        _, n_y, n_z = [n_xyz[..., i] for i in range(3)]
        norm = torch.sqrt(eps + n_y ** 2 + n_z ** 2)
        sin_n = -n_z / norm
        cos_n = n_y / norm

        n_rots = sin_c2.new_zeros((*sin_c2.shape, 3, 3))
        n_rots[..., 0, 0] = 1
        n_rots[..., 1, 1] = cos_n
        n_rots[..., 1, 2] = -1 * sin_n
        n_rots[..., 2, 1] = sin_n
        n_rots[..., 2, 2] = cos_n

        rots = rot_matmul(n_rots, c_rots)

        rots = rots.transpose(-1, -2)
        translation = -1 * translation

        return T(rots, translation)

    def cuda(self) -> T:
        """
            Moves the transformation object to GPU memory

            Returns:
                A version of the transformation on GPU
        """
        return T(self.rots.cuda(), self.trans.cuda())

'''
_quat_elements = ["a", "b", "c", "d"]
_qtr_keys = [l1 + l2 for l1 in _quat_elements for l2 in _quat_elements]
_qtr_ind_dict = {key: ind for ind, key in enumerate(_qtr_keys)}


def _to_mat(pairs):
    mat = np.zeros((4, 4))
    for pair in pairs:
        key, value = pair
        ind = _qtr_ind_dict[key]
        mat[ind // 4][ind % 4] = value

    return mat


_qtr_mat = np.zeros((4, 4, 3, 3))
_qtr_mat[..., 0, 0] = _to_mat([("aa", 1), ("bb", 1), ("cc", -1), ("dd", -1)])
_qtr_mat[..., 0, 1] = _to_mat([("bc", 2), ("ad", -2)])
_qtr_mat[..., 0, 2] = _to_mat([("bd", 2), ("ac", 2)])
_qtr_mat[..., 1, 0] = _to_mat([("bc", 2), ("ad", 2)])
_qtr_mat[..., 1, 1] = _to_mat([("aa", 1), ("bb", -1), ("cc", 1), ("dd", -1)])
_qtr_mat[..., 1, 2] = _to_mat([("cd", 2), ("ab", -2)])
_qtr_mat[..., 2, 0] = _to_mat([("bd", 2), ("ac", -2)])
_qtr_mat[..., 2, 1] = _to_mat([("cd", 2), ("ab", 2)])
_qtr_mat[..., 2, 2] = _to_mat([("aa", 1), ("bb", -1), ("cc", -1), ("dd", 1)])


def quat_to_rot(quat: torch.Tensor) -> torch.Tensor:
    """
        Converts a quat to a rotation matrix.

        Args:
            quat: [*, 4] quats
        Returns:
            [*, 3, 3] rotation matrices
    """
    # [*, 4, 4]
    quat = quat[..., None] * quat[..., None, :]

    # [4, 4, 3, 3]
    mat = quat.new_tensor(_qtr_mat)

    # [*, 4, 4, 3, 3]
    shaped_qtr_mat = mat.view((1,) * len(quat.shape[:-2]) + mat.shape)
    quat = quat[..., None, None] * shaped_qtr_mat

    # [*, 3, 3]
    return torch.sum(quat, dim=(-3, -4))


def affine_vector_to_4x4(vector: torch.Tensor) -> torch.Tensor:
    """
        Transforms a tensor whose final dimension has the form:

            [*quat, *translation]

        into a homogenous transformation tensor.

        Args:
            vector: [*, 7] input tensor
        Returns:
            [*, 4, 4] homogenous transformation tensor
    """
    quats = vector[..., :4]
    trans = vector[..., 4:]

    four_by_four = vector.new_zeros((*vector.shape[:-1], 4, 4))
    four_by_four[..., :3, :3] = quat_to_rot(quats)
    four_by_four[..., :3, 3] = trans
    four_by_four[..., 3, 3] = 1

    return four_by_four

def A_transpose_matrix(alpha,device):
    return torch.tensor([[torch.cos(alpha), torch.sin(alpha)],
                     [-torch.sin(alpha), torch.cos(alpha)]],device=device)

def S_vec(alpha,device):
    return torch.tensor([[torch.cos(alpha)],
                     [torch.sin(alpha)]],device=device)

def get_dihedrals(coords,atom_idx):
    a, b, c, d = coords[atom_idx]
    b0 = -1.0*(b - a)
    b1 = c - b
    b2 = d - c
    b1 = b1 / (torch.linalg.norm(b1, axis=-1)+1e-6)

    v = b0 - torch.sum(b0*b1, axis=-1)*b1
    w = b2 - torch.sum(b2*b1, axis=-1)*b1

    x = torch.sum(v*w, axis=-1)
    y = torch.sum(torch.cross(b1, v)*w, axis=-1)

    angle = torch.arctan2(y, x)
    return angle

def get_dihedral_vonMises(mol, coords, pred_coords, atom_idx):
    v = coords.new_zeros((2,1))
    iAtom = mol.GetAtomWithIdx(atom_idx[1])
    jAtom = mol.GetAtomWithIdx(atom_idx[2])
    k_0 = atom_idx[0]
    i = atom_idx[1]
    j = atom_idx[2]
    l_0 = atom_idx[3]
    for b1 in iAtom.GetBonds():
        k = b1.GetOtherAtomIdx(i)
        if k == j:
            continue
        for b2 in jAtom.GetBonds():
            l = b2.GetOtherAtomIdx(j)
            if l == i:
                continue
            assert k != l
            s_star = S_vec(get_dihedrals(pred_coords, [k, i, j, l]),v.device)
            a_mat = A_transpose_matrix(get_dihedrals(coords, [k, i, j, k_0]) + get_dihedrals(coords, [l_0, i, j, l]),v.device)
            v = v + torch.matmul(a_mat, s_star)
    v = v / (torch.linalg.norm(v)+1e-6)
    v = v.reshape(-1)
    return torch.arctan2(v[1], v[0])

def quat_to_axis_angle(quats: torch.Tensor) -> torch.Tensor:
    """
    Convert rotations given as quats to axis/angle.

    Args:
        quats: quats with real part first,
            as tensor of shape (..., 4).

    Returns:
        Rotations given as a vector in axis angle form, as a tensor
            of shape (..., 3), where the magnitude is the angle
            turned anticlockwise in radians around the vector's
            direction.
    """
    norms = torch.norm(quats[..., 1:], p=2, dim=-1, keepdim=True)
    half_angles = torch.atan2(norms, quats[..., :1])
    angles = 2 * half_angles
    eps = 1e-6
    small_angles = angles.abs() < eps
    sin_half_angles_over_angles = torch.empty_like(angles)
    sin_half_angles_over_angles[~small_angles] = (
        torch.sin(half_angles[~small_angles]) / angles[~small_angles]
    )
    # for x small, sin(x/2) is about x/2 - (x/2)^3/6
    # so sin(x/2)/x is about 1/2 - (x*x)/48
    sin_half_angles_over_angles[small_angles] = (
        0.5 - (angles[small_angles] * angles[small_angles]) / 48
    )
    return quats[..., 1:] / sin_half_angles_over_angles

def quat_to_matrix(quats: torch.Tensor) -> torch.Tensor:
    """
    Convert rotations given as quats to rotation matrices.

    Args:
        quats: quats with real part first,
            as tensor of shape (..., 4).

    Returns:
        Rotation matrices as tensor of shape (..., 3, 3).
    """
    r, i, j, k = torch.unbind(quats, -1)
    two_s = 2.0 / (quats * quats).sum(-1)

    o = torch.stack(
        (
            1 - two_s * (j * j + k * k),
            two_s * (i * j - k * r),
            two_s * (i * k + j * r),
            two_s * (i * j + k * r),
            1 - two_s * (i * i + k * k),
            two_s * (j * k - i * r),
            two_s * (i * k - j * r),
            two_s * (j * k + i * r),
            1 - two_s * (i * i + j * j),
        ),
        -1,
    )
    return o.reshape(quats.shape[:-1] + (3, 3))


def axis_angle_to_matrix(axis_angle: torch.Tensor) -> torch.Tensor:
    """
    Convert rotations given as axis/angle to rotation matrices.

    Args:
        axis_angle: Rotations given as a vector in axis angle form,
            as a tensor of shape (..., 3), where the magnitude is
            the angle turned anticlockwise in radians around the
            vector's direction.

    Returns:
        Rotation matrices as tensor of shape (..., 3, 3).
    """
    return quat_to_matrix(axis_angle_to_quat(axis_angle))

def _sqrt_positive_part(x: torch.Tensor) -> torch.Tensor:
    """
    Returns torch.sqrt(torch.max(0, x))
    but with a zero subgradient where x is 0.
    """
    ret = torch.zeros_like(x)
    positive_mask = x > 0
    ret[positive_mask] = torch.sqrt(x[positive_mask])
    return ret

def rot_to_quat(matrix: torch.Tensor) -> torch.Tensor:
    """
    Convert rotations given as rotation matrices to quats.

    Args:
        matrix: Rotation matrices as tensor of shape (..., 3, 3).

    Returns:
        quats with real part first, as tensor of shape (..., 4).
    """
    if matrix.size(-1) != 3 or matrix.size(-2) != 3:
        raise ValueError(f"Invalid rotation matrix shape {matrix.shape}.")

    batch_dim = matrix.shape[:-2]
    m00, m01, m02, m10, m11, m12, m20, m21, m22 = torch.unbind(
        matrix.reshape(batch_dim + (9,)), dim=-1
    )

    q_abs = _sqrt_positive_part(
        torch.stack(
            [
                1.0 + m00 + m11 + m22,
                1.0 + m00 - m11 - m22,
                1.0 - m00 + m11 - m22,
                1.0 - m00 - m11 + m22,
            ],
            dim=-1,
        )
    )

    # we produce the desired quat multiplied by each of r, i, j, k
    quat_by_rijk = torch.stack(
        [
            torch.stack([q_abs[..., 0] ** 2, m21 - m12, m02 - m20, m10 - m01], dim=-1),
            torch.stack([m21 - m12, q_abs[..., 1] ** 2, m10 + m01, m02 + m20], dim=-1),
            torch.stack([m02 - m20, m10 + m01, q_abs[..., 2] ** 2, m12 + m21], dim=-1),
            torch.stack([m10 - m01, m20 + m02, m21 + m12, q_abs[..., 3] ** 2], dim=-1),
        ],
        dim=-2,
    )

    # We floor here at 0.1 but the exact level is not important; if q_abs is small,
    # the candidate won't be picked.
    flr = torch.tensor(0.1).to(dtype=q_abs.dtype, device=q_abs.device)
    quat_candidates = quat_by_rijk / (2.0 * q_abs[..., None].max(flr))

    # if not for numerical problems, quat_candidates[i] should be same (up to a sign),
    # forall i; we pick the best-conditioned one (with the largest denominator)

    return quat_candidates[
        F.one_hot(q_abs.argmax(dim=-1), num_classes=4) > 0.5, :  # pyre-ignore[16]
    ].reshape(batch_dim + (4,))

def matrix_to_axis_angle(matrix: torch.Tensor) -> torch.Tensor:
    """
    Convert rotations given as rotation matrices to axis/angle.

    Args:
        matrix: Rotation matrices as tensor of shape (..., 3, 3).

    Returns:
        Rotations given as a vector in axis angle form, as a tensor
            of shape (..., 3), where the magnitude is the angle
            turned anticlockwise in radians around the vector's
            direction.
    """
    return quat_to_axis_angle(rot_to_quat(matrix))

def axis_angle_to_quat(axis_angle: torch.Tensor) -> torch.Tensor:
    """
    Convert rotations given as axis/angle to quats.

    Args:
        axis_angle: Rotations given as a vector in axis angle form,
            as a tensor of shape (..., 3), where the magnitude is
            the angle turned anticlockwise in radians around the
            vector's direction.

    Returns:
        quats with real part first, as tensor of shape (..., 4).
    """
    angles = torch.norm(axis_angle, p=2, dim=-1, keepdim=True)
    half_angles = angles * 0.5
    eps = 1e-6
    small_angles = angles.abs() < eps
    sin_half_angles_over_angles = torch.empty_like(angles)
    sin_half_angles_over_angles[~small_angles] = (
        torch.sin(half_angles[~small_angles]) / angles[~small_angles]
    )
    # for x small, sin(x/2) is about x/2 - (x/2)^3/6
    # so sin(x/2)/x is about 1/2 - (x*x)/48
    sin_half_angles_over_angles[small_angles] = (
        0.5 - (angles[small_angles] * angles[small_angles]) / 48
    )
    quats = torch.cat(
        [torch.cos(half_angles), axis_angle * sin_half_angles_over_angles], dim=-1
    )
    return quats

def modify_conformer(pos, edge_index, mask_rotate, torsion_updates):
    for idx_edge, e in enumerate(edge_index):
        if -1e-3 < torsion_updates[idx_edge] < 1e-3:
            continue
        u, v = e[0], e[1]

        # check if need to reverse the edge, v should be connected to the part that gets rotated
        assert not mask_rotate[idx_edge, u]
        assert mask_rotate[idx_edge, v]

        rot_vec = pos[v] - pos[u]
        rot_vec = rot_vec * torsion_updates[idx_edge] / (torch.linalg.norm(rot_vec)+1e-6)
        rot_mat = axis_angle_to_matrix(rot_vec)

        pos[:mask_rotate.shape[1]][mask_rotate[idx_edge]] = (pos[:mask_rotate.shape[1]][mask_rotate[idx_edge]] - pos[u]) @ rot_mat.T + pos[u]

    return pos
'''
