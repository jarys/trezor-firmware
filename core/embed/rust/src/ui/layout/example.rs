use crate::{
    micropython::obj::Obj,
    ui::{
        component::{Button, Child, Component, Dialog, DialogMsg, Never, Text},
        display, theme,
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
extern "C" fn ui_layout_new_example() -> Obj {
    LayoutObj::new(Child::new(Dialog::new(
        display::screen(),
        |area| {
            Text::new(area)
                .format("Testing text layout, with some text, and some more text. And {param}")
                .with(b"param", b"parameters!")
        },
        |area| Button::with_text(area, b"Left", theme::button_default()),
        |area| Button::with_text(area, b"Right", theme::button_default()),
    )))
    .into()
}
