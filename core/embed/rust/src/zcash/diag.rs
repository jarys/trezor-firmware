use crate::micropython::obj::Obj;
use crate::zcash::orchard::benchmarks;
use core::convert::TryFrom;

#[no_mangle]
pub extern "C" fn zcash_diag(_ins: Obj, data: Obj) -> Obj {
    let ins = u64::try_from(_ins).unwrap();
    for _ in 0..ins {
        benchmarks::sinsemilla();
    }
    data
}
