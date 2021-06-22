use crate::ui::math::{Grid, Rect};

use super::{
    button::{Button, ButtonMsg::Clicked},
    component::{Child, Component, Event, EventCtx},
};

pub enum ConfirmMsg<T: Component> {
    Content(T::Msg),
    LeftClicked,
    RightClicked,
}

pub struct Confirm<T> {
    content: Child<T>,
    left_btn: Option<Child<Button>>,
    right_btn: Option<Child<Button>>,
}

impl<T: Component> Confirm<T> {
    pub fn new(
        area: Rect,
        content: impl FnOnce(Rect) -> T,
        left: impl FnOnce(Rect) -> Button,
        right: impl FnOnce(Rect) -> Button,
    ) -> Self {
        let grid = Grid::new(area, 5, 2);
        let content = Child::new(content(Rect::new(
            grid.row_col(0, 0).top_left(),
            grid.row_col(4, 1).bottom_right(),
        )));
        let left_btn = Child::new(left(grid.row_col(4, 0)));
        let right_btn = Child::new(right(grid.row_col(4, 1)));
        Self {
            content,
            left_btn: Some(left_btn),
            right_btn: Some(right_btn),
        }
    }
}

impl<T: Component> Component for Confirm<T> {
    type Msg = ConfirmMsg<T>;

    fn event(&mut self, ctx: &mut EventCtx, event: Event) -> Option<Self::Msg> {
        if let Some(msg) = self.content.event(ctx, event) {
            Some(ConfirmMsg::Content(msg))
        } else if let Some(Clicked) = self.left_btn.as_mut().and_then(|b| b.event(ctx, event)) {
            Some(ConfirmMsg::LeftClicked)
        } else if let Some(Clicked) = self.right_btn.as_mut().and_then(|b| b.event(ctx, event)) {
            Some(ConfirmMsg::RightClicked)
        } else {
            None
        }
    }

    fn paint(&mut self) {
        self.content.paint();
        self.left_btn.as_mut().map(|b| b.paint());
        self.right_btn.as_mut().map(|b| b.paint());
    }
}
