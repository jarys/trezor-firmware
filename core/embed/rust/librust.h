#include "librust_qstr.h"

mp_obj_t protobuf_type_for_name(mp_obj_t name);
mp_obj_t protobuf_type_for_wire(mp_obj_t wire_id);
mp_obj_t protobuf_decode(mp_obj_t buf, mp_obj_t def,
                         mp_obj_t enable_experimental);
mp_obj_t protobuf_len(mp_obj_t obj);
mp_obj_t protobuf_encode(mp_obj_t buf, mp_obj_t obj);

#ifdef TREZOR_EMULATOR
mp_obj_t protobuf_debug_msg_type();
mp_obj_t protobuf_debug_msg_def_type();
#endif

mp_obj_t ui_layout_new_example(mp_obj_t);
mp_obj_t ui_layout_new_confirm_action(size_t n_args, const mp_obj_t *args,
                                      mp_map_t *kwargs);

#ifdef TREZOR_EMULATOR
mp_obj_t ui_debug_layout_type();
#endif

mp_obj_t orchardlib_diag(mp_obj_t ins, mp_obj_t data);
mp_obj_t orchardlib_derive_full_viewing_key(mp_obj_t spending_key, mp_obj_t internal);
mp_obj_t orchardlib_derive_internal_full_viewing_key(mp_obj_t full_viewing_key);
mp_obj_t orchardlib_derive_incoming_viewing_key(mp_obj_t full_viewing_key, mp_obj_t internal);
mp_obj_t orchardlib_derive_outgoing_viewing_key(mp_obj_t full_viewing_key, mp_obj_t internal);
mp_obj_t orchardlib_derive_address(mp_obj_t full_viewing_key, mp_obj_t diversifier_index, mp_obj_t internal);
mp_obj_t orchardlib_f4jumble(mp_obj_t message);
mp_obj_t orchardlib_f4jumble_inv(mp_obj_t message);
mp_obj_t orchardlib_shield(mp_obj_t action_info, mp_obj_t rng_config);
mp_obj_t orchardlib_sign(mp_obj_t spending_key, mp_obj_t alpha, mp_obj_t sighash);
mp_obj_t orchardlib_randint(mp_obj_t max, mp_obj_t rng_config);