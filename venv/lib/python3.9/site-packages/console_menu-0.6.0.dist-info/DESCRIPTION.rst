|Build Status|\ |Documentation Status|

console-menu
============

A simple Python menu-based UI system for terminal applications.
Perfect for those times when you need a menu-driven program, but don’t want the
overhead or learning curve of a full-fledged GUI framework.

Derived from the curses-menu project, but with curses dependency removed.

http://console-menu.readthedocs.org/en/latest/

.. image:: ./images/console-menu_screenshot1.png

.. image:: ./images/console-menu_screenshot2.png


Installation
~~~~~~~~~~~~

Tested on Python 2.7, 3.4, 3.5, and 3.6, as well as pypy and pypy 3.

Installation can be performed by running pip

.. code:: shell

   pip install console-menu

Usage
-----

It's designed to be pretty simple to use. Here's an example

.. code:: python

    # Import the necessary packages
    from consolemenu import *
    from consolemenu.items import *

    # Create the menu
    menu = ConsoleMenu("Title", "Subtitle")

    # Create some items

    # MenuItem is the base class for all items, it doesn't do anything when selected
    menu_item = MenuItem("Menu Item")

    # A FunctionItem runs a Python function when selected
    function_item = FunctionItem("Call a Python function", input, ["Enter an input"])

    # A CommandItem runs a console command
    command_item = CommandItem("Run a console command",  "touch hello.txt")

    # A SelectionMenu constructs a menu from a list of strings
    selection_menu = SelectionMenu(["item1", "item2", "item3"])

    # A SubmenuItem lets you add a menu (the selection_menu above, for example)
    # as a submenu of another menu
    submenu_item = SubmenuItem("Submenu item", selection_menu, menu)

    # Once we're done creating them, we just add the items to the menu
    menu.append_item(menu_item)
    menu.append_item(function_item)
    menu.append_item(command_item)
    menu.append_item(submenu_item)

    # Finally, we call show to show the menu and allow the user to interact
    menu.show()

.. |Build Status| image:: https://travis-ci.org/aegirhall/console-menu.svg
   :target: https://travis-ci.org/aegirhall/console-menu
.. |Documentation Status| image:: https://readthedocs.org/projects/console-menu/badge/?version=latest
   :target: http://console-menu.readthedocs.org/en/latest/?badge=latest

v0.6.0 (2019-09-07)
===================
- Fix issue #28, allow console screen argument for SelectionMenu.
- Fix issue #22, allow custom exit text for main menu.
- Fix issue #19, failure to clear screen using Windows 10 SSH.
- Potentially Breaking Change: reverted screen.input() method to return the
  simple string value, as it did in v0.4.0 and prior. Moved the InputResult
  tuple for input validation to the PromptUtils class.
- Expanding documentation and converting to Google-style docstrings (WIP).
- Add flush() method to screen.

v0.5.1 (2018-11-18)
===================
- Remove unnecessary imports (#10).

v0.5.0 (2018-11-02)
===================
- Add new input validation feature, contributed by DaBbleR23.
- Add feature to allow menu item removal.
- Add feature to allow user to cancel input.
- Remove external readline dependency.

v0.4.0 (2018-03-13)
===================
- Add feature to hide borders for menu items.
- Add feature to return to previous menu.
- Add printf and println functions to prompt_utils.

v0.3.0 (2018-03-09)
===================
- Add prompt_utils class.
- Add feature to show borders above or below menu items.
- Fix unit tests to run on windows.
- Add new borders for heavy outer/light inner; and double-line outer/light inner.

v0.2.0 (2018-03-09)
===================
- Add new multi-select menu feature.
- Use editable flag for installing project.
- Clean up imports.
- Expanded unit tests.
- Change doc theme to sphinx_rtd_theme.

v0.1.0 (2018-03-08)
===================
- Add Python 2.7, 3.5, and 3.6 to build matrix.
- Remove Python 2.6, 3.3, 3.4.
- PEP8 cleanup.
- Add pycodestyle to build process.
- Expanded unit tests.
- Add updated screenshots for Readme.
- Enhance text section to allow multi-line wrapping.
- Expand examples to show more features.
- Fix bug in heavy borders showing incorrect characters.
- Add optional bottom border to header section.
- Add prologue and epilogue sections to menus.
- Add methods for setting the border style factory and style type.
- Add border style type enumeration and factory.
- Change default padding for left and right to 2.
- Add new double-line border and rename border styles for consistency.
- Change default prompt.
- Update screen input method for python2 & 3 compatibility
- Remove deprecated methods
- Change sphinx theme and fix errors in rst files.
- Fix warnings/errors uncovered by pytest.
- Add unicode heavy border style.
- Add menu formatter class and related changes.
- Remove curses dependency.
- Initial commit of project, forked from curses-menu.



