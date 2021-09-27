/*
 * This file is part of the Trezor project, https://trezor.io/
 *
 * Copyright (c) SatoshiLabs
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "py/runtime.h"

#if MICROPY_PY_TREZORCRYPTO

#include "librust.h"


STATIC MP_DEFINE_CONST_FUN_OBJ_1(mod_orchard_shield,
                                 orchard_shield);

STATIC const mp_rom_map_elem_t mp_module_trezororchard_globals_table[] = {
    {MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_trezororchard)},

    {MP_ROM_QSTR(MP_QSTR_shield),
     MP_ROM_PTR(&mod_orchard_shield)},

};

STATIC MP_DEFINE_CONST_DICT(mp_module_trezororchard_globals,
                            mp_module_trezororchard_globals_table);

const mp_obj_module_t mp_module_trezororchard = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&mp_module_trezororchard_globals,
};

MP_REGISTER_MODULE(MP_QSTR_trezororchard, mp_module_trezororchard,
                   MICROPY_PY_TREZORCRYPTO);

#endif  // MICROPY_PY_TREZOCRYPTO