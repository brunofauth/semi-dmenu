#! /usr/bin/env python3
# TODO: swap tk.Listbox for ttk.TreeView


from tkinter import *
from tkinter import ttk
from typing import Sequence, Callable, Optional

import thefuzz.process as tfp
import sys


FUZZY_STR_THRESHOLD = .9


class DynamicCircularRange:

    def __init__(self, lower_fac: Callable[[], int], upper_fac: Callable[[], int], init: Optional[int]=None):
        self._lower_bound_factory = lower_fac
        self._upper_bound_factory = upper_fac

        init = init or self.lower_bound
        self.raise_if_out_of_bounds(init)
        self.current = init

    def __contains__(self, value: int) -> bool:
        if not isinstance(value, int):
            raise TypeError("'value' must be an integer.")
        return self.lower_bound <= value < self.upper_bound

    def raise_if_out_of_bounds(self, value: int) -> None:
        if value not in self:
            raise ValueError(f"{value=} is outside of [{self.lower_bound},{self.upper_bound}[")

    @property
    def lower_bound(self):
        return self._lower_bound_factory()

    @property
    def upper_bound(self):
        return self._upper_bound_factory()

    @property
    def next(self):
        self.current += 1
        if self.current >= self.upper_bound:
            self.current = self.lower_bound
        return self.current

    @property
    def prev(self):
        self.current -= 1
        if self.current < self.lower_bound:
            self.current = self.upper_bound - 1
        return self.current


def on_query_change(query_var: StringVar, choices: Sequence[str], choices_var: StringVar, options_box: Listbox) -> Callable:
    def callback(*_) -> None:
        options_box.selection_clear(0, END)
        options_box.select_set(0)
        options_box.see(0)
        if not len(query_var.get()):
            choices_var.set(choices)
        else:
            data = tfp.extract(query_var.get(), choices)
            choices_var.set([s for s, w in data if w >= FUZZY_STR_THRESHOLD])
    return callback


def on_select_entry(choices_var: StringVar, box: Listbox) -> Callable:
    def callback(*_) -> None:
        choices = eval(choices_var.get())
        for index in box.curselection():
            print(choices[index])
        raise SystemExit
    return callback


def on_prev_item(ranje: DynamicCircularRange, box: Listbox) -> Callable:
    def callback(*_) -> None:
        box.selection_clear(ranje.lower_bound, ranje.upper_bound)
        box.selection_set(ranje.prev)
        box.see(ranje.current)
    return callback


def on_next_item(ranje: DynamicCircularRange, box: Listbox) -> Callable:
    def callback(*_) -> None:
        box.selection_clear(ranje.lower_bound, ranje.upper_bound)
        box.selection_set(ranje.next)
        box.see(ranje.current)
    return callback


def on_escape(query_str: StringVar) -> None:
    def callback(*_) -> None:
        if query_str.get():
            query_str.set("")
        else:
            raise SystemExit
    return callback


def create_menu(choices: Sequence[str]) -> Tk:
    root = Tk()
    root.title("Pick an Entry")
    root.geometry("320x240")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    root_frame = ttk.Frame(root)
    root_frame.grid(column=0, row=0, sticky=(N, S, E, W))
    root_frame.columnconfigure(0, weight=1)
    root_frame.rowconfigure(1, weight=1)

    chosen_option = StringVar(value=choices)
    options_box = Listbox(root_frame, height=10, listvariable=chosen_option)
    options_box.grid(column=0, row=1, sticky=(N, S, E, W))
    options_box.select_set(0)

    option_idx = DynamicCircularRange(lambda: 0, lambda: len(eval(chosen_option.get())))

    query_str = StringVar()
    query_entry = ttk.Entry(root_frame, textvariable=query_str)
    query_entry.grid(column=0, row=0, sticky=(N, S, E, W))
    query_entry.focus()
    query_str.trace_add("write", on_query_change(query_str, choices, chosen_option, options_box))

    root.bind("<Up>", on_prev_item(option_idx, options_box))
    root.bind("<Down>", on_next_item(option_idx, options_box))
    root.bind("<Left>", on_prev_item(option_idx, options_box))
    root.bind("<Right>", on_next_item(option_idx, options_box))
    root.bind("<Return>", on_select_entry(chosen_option, options_box))
    root.bind("<Escape>", on_escape(query_str))

    return root


def main(choices: list[str]) -> None:
    if not len(choices):
        return
    create_menu(choices).mainloop()


if __name__ == "__main__":
    main([line.strip() for line in sys.stdin])

