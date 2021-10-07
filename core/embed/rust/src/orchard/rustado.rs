//#![no_std]
use core::convert::{TryFrom, TryInto};

use core::ops::Deref;

//#[macro_use] extern crate slice_as_array;
//slice_as_array = { version = "1.1.0", default-features = false }

use pasta_curves::arithmetic::CurveExt;
use pasta_curves::group::GroupEncoding;
use pasta_curves::pallas;

use sinsemilla_trezor::HashDomain;

use crate::{
    micropython::{buffer::Buffer, obj::Obj},
    util,
};

//use static_alloc::Bump;

//#[global_allocator]
//static A: Bump<[u8; 1 << 13]> = Bump::uninit(); // 8kB heap

#[no_mangle]
pub extern "C" fn orchard_shield(plain: Obj) -> Obj {
    let block = || {
        /**
        {
            extern crate alloc;
            use alloc::boxed::Box;
            let a = Box::new(4);
        } // */
        let buf = Buffer::try_from(plain)?;
        let mut bytes: [u8; 32] = buf.deref().try_into().unwrap();
        //let bytes = slice_as_array!(bytes, [u8; 32]).expect("bad hash length");
        let p = pallas::Point::from_bytes(&bytes);
        // &[ 158, 65, 96, 245, 29, 17, 127, 195, 173, 55, 35, 94, 62, 5, 60, 89, 166, 171, 225, 188,71, 252, 108, 156, 170, 69, 105, 85, 77, 30, 136, 10]).unwrap();
        //for _ in 0..25 {
        //    p = p + p;
        //}
        let p: pallas::Point = pallas::Point::unboxed_hash_to_curve("domain", b"Hello");

        let domain = HashDomain::new("test");
        let message = [
            true, true, false, true, false, true, false, true, false, true, true,
        ]
        .iter()
        .cloned();
        let p = domain.hash_to_point(message).unwrap();

        let arr = p.to_bytes();

        let sl: &[u8] = &arr;
        let obj = Obj::try_from(sl)?;

        let normal: [u8; 48] = [
            0x5d, 0x7a, 0x8f, 0x73, 0x9a, 0x2d, 0x9e, 0x94, 0x5b, 0x0c, 0xe1, 0x52, 0xa8, 0x04,
            0x9e, 0x29, 0x4c, 0x4d, 0x6e, 0x66, 0xb1, 0x64, 0x93, 0x9d, 0xaf, 0xfa, 0x2e, 0xf6,
            0xee, 0x69, 0x21, 0x48, 0x1c, 0xdd, 0x86, 0xb3, 0xcc, 0x43, 0x18, 0xd9, 0x61, 0x4f,
            0xc8, 0x20, 0x90, 0x5d, 0x04, 0x2b,
        ];
        let _normal_sl: &[u8] = &normal;

        //let p: pallas::Point = pallas::Point::unboxed_hash_to_curve("domain", b"Hello");
        //let p_bytes = p.to_bytes();
        //let obj = Obj::try_from(&p_bytes[..])?;
        //let hash_pallas = pallas::Point::hash_to_curve("z.cash:test");
        //let mut us = [Field::zero(); 2];
        //let hx = hashtocurve::hash_to_field("pallas", "neco", [1,2,3], &mut us);

        Ok(obj)
    };

    unsafe { util::try_or_raise(block) }
}
