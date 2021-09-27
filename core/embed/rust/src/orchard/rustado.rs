use core::convert::{TryFrom, TryInto};
use core::str;
use core::{
    ops::{Deref, DerefMut},
    ptr, slice,
};

//#[macro_use] extern crate slice_as_array;
//slice_as_array = { version = "1.1.0", default-features = false }

use pasta_curves::arithmetic::Field;
use pasta_curves::pallas;
use pasta_curves::group::ff::PrimeField;
use pasta_curves::group::GroupEncoding;

use crate::{
    error::Error,
    micropython::{buffer::Buffer, gc::Gc, list::List, map::Map, obj::Obj, qstr::Qstr},
    util,
};

#[no_mangle]
pub extern "C" fn orchard_shield(plain: Obj) -> Obj {
    util::try_or_raise(|| {
        let buf = Buffer::try_from(plain)?;
        let bytes : &[u8] = buf.deref();
        //let bytes = slice_as_array!(bytes, [u8; 32]).expect("bad hash length");
        let mut p = pallas::Point::from_bytes(&[ 158, 65, 96, 245, 29, 17, 127, 195, 173, 55, 35, 94, 62, 5, 60, 89, 166, 171, 225, 188,71, 252, 108, 156, 170, 69, 105, 85, 77, 30, 136, 10]).unwrap();
        for _ in (0..25600000) {
            p = p + p;
        }
        let arr = p.to_bytes();
        let sl: &[u8] = &arr;
        let obj = Obj::from(sl);

        let normal : [u8; 48] = [
            0x5d, 0x7a, 0x8f, 0x73, 0x9a, 0x2d, 0x9e, 0x94, 0x5b, 0x0c, 0xe1, 0x52, 0xa8, 0x04,
            0x9e, 0x29, 0x4c, 0x4d, 0x6e, 0x66, 0xb1, 0x64, 0x93, 0x9d, 0xaf, 0xfa, 0x2e, 0xf6,
            0xee, 0x69, 0x21, 0x48, 0x1c, 0xdd, 0x86, 0xb3, 0xcc, 0x43, 0x18, 0xd9, 0x61, 0x4f,
            0xc8, 0x20, 0x90, 0x5d, 0x04, 0x2b,
        ];
        let normal_sl : &[u8] = &normal;


        //let hash_pallas = pallas::Point::hash_to_curve("z.cash:test");
        //let mut us = [Field::zero(); 2];
        //let hx = hashtocurve::hash_to_field("pallas", "neco", [1,2,3], &mut us);


        Ok(obj)
    })
} 