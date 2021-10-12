use sinsemilla_trezor::HashDomain;

pub fn sinsemilla() {
    let domain = HashDomain::new("benchmark");
    let input = core::iter::repeat(true).take(1000);
    let _ = domain.hash_to_point(input);
}
