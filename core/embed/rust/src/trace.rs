pub trait Tracer {
    fn bytes(&mut self, b: &[u8]);
    fn str(&mut self, s: &str);
    fn tag(&mut self, t: &str);
    fn open(&mut self, name: &str);
    fn field(&mut self, name: &str, value: &dyn Trace);
    fn close(&mut self);
}

pub trait Trace {
    fn trace(&self, d: &mut dyn Tracer);
}

impl Trace for &[u8] {
    fn trace(&self, t: &mut dyn Tracer) {
        t.bytes(self);
    }
}

impl Trace for &str {
    fn trace(&self, t: &mut dyn Tracer) {
        t.str(self);
    }
}

impl<T> Trace for Option<T>
where
    T: Trace,
{
    fn trace(&self, d: &mut dyn Tracer) {
        match self {
            Some(v) => v.trace(d),
            None => d.tag("None"),
        }
    }
}
