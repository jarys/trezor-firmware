use core::convert::TryInto;

use crate::{
    micropython::{buffer::Buffer, obj::Obj},
    ui::{
        component::{
            model_tt::{theme, Button, Dialog, DialogMsg, Text},
            Child, Component, Never,
        },
        display,
    },
};

use super::obj::LayoutObj;

impl<T> From<DialogMsg<T>> for Obj
where
    T: Component,
    T::Msg: Into<Obj>,
{
    fn from(val: DialogMsg<T>) -> Self {
        match val {
            DialogMsg::Content(c) => c.into(),
            DialogMsg::LeftClicked => 1.into(),
            DialogMsg::RightClicked => 2.into(),
        }
    }
}

impl From<Never> for Obj {
    fn from(_: Never) -> Self {
        unreachable!()
    }
}

#[no_mangle]
extern "C" fn ui_layout_new_example(param: Obj) -> Obj {
    let param: Buffer = param.try_into().unwrap();

    LayoutObj::new(Child::new(Dialog::new(
        display::screen(),
        |area| {
            Text::new(area, param)
                .with(b"some", "a few")
                .with(b"param", "xx")
        },
        |area| Button::with_text(area, b"Left", theme::button_default()),
        |area| Button::with_text(area, b"Right", theme::button_default()),
    )))
    .into()
}

#[cfg(test)]
mod tests {
    use crate::trace::{Trace, Tracer};

    use super::*;

    impl Tracer for Vec<u8> {
        fn bytes(&mut self, b: &[u8]) {
            self.extend(b)
        }

        fn string(&mut self, s: &str) {
            self.extend(s.as_bytes())
        }

        fn symbol(&mut self, name: &str) {
            self.extend(name.as_bytes())
        }

        fn open(&mut self, name: &str) {
            self.extend(b"<");
            self.extend(name.as_bytes());
            self.extend(b" ");
        }

        fn field(&mut self, name: &str, value: &dyn Trace) {
            self.extend(name.as_bytes());
            self.extend(b":");
            value.trace(self);
            self.extend(b" ");
        }

        fn close(&mut self) {
            self.extend(b">")
        }
    }

    fn trace(val: &impl Trace) -> String {
        let mut t = Vec::new();
        val.trace(&mut t);
        String::from_utf8(t).unwrap()
    }

    #[test]
    fn trace_example_layout() {
        let layout = Child::new(Dialog::new(
            display::screen(),
            |area| {
                Text::new(
                    area,
                    "Testing text layout, with some text, and some more text. And {param}",
                )
                .with(b"param", b"parameters!")
            },
            |area| Button::with_text(area, b"Left", theme::button_default()),
            |area| Button::with_text(area, b"Right", theme::button_default()),
        ));
        assert_eq!(
            trace(&layout),
            r#"<Dialog content:<Text content:Testing text layout, with
some text, and some more
text. And parameters! > left:<Button text:Left > right:<Button text:Right > >"#
        )
    }
}
