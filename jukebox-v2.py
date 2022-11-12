"""update ver of jukebox"""
import sqlite3
import tkinter


class Scrollbox(tkinter.Listbox):

    def __init__(self, window, **kwargs):
        super().__init__(window, **kwargs)
        self.scrollbar = tkinter.Scrollbar(window, orient=tkinter.VERTICAL, command=self.yview)

    def grid(self, row, column, sticky='nsw', rowspan=1, columnspan=1, **kwargs):
        super().grid(row=row, column=column, sticky=sticky, rowspan=rowspan, columnspan=columnspan, **kwargs)
        self.scrollbar.grid(row=row, column=column, sticky='nse', rowspan=rowspan)
        self['yscrollcommand'] = self.scrollbar.set


class DataListBox(Scrollbox):
    """DataListBox is upgrade of ScrollBox with function call on_select to execute when one item is selected,
    it also auto create sql to set up stuffs
    new attribute:
        linked_table : link to the child table
        link_field : hold the field name to link between 2 table
        link_value : value from master - see more plain in implement
        sql_select : string which is SQLite statement to select data in its ListBox
        sort_order : string which is SQLite statement to define the other when output data
    """
    def __init__(self, window, connection, table_name, data_field, sort_order=(), **kwargs):
        """init the stuff, linked_table and link_field is defined later,
         it binds the select event of current table to on_select method"""
        super().__init__(window, **kwargs)

        self.linked_table = None
        self.link_field = None
        self.link_value = None

        self.cursor = connection.cursor()
        self.table_name = table_name
        self.data_field = data_field

        self.bind('<<ListboxSelect>>', self.on_select)

        self.sql_select = "SELECT " + self.data_field + ", _id" + " FROM " + self.table_name
        if sort_order:
            self.sql_sort = " ORDER BY " + ','.join(sort_order)
        else:
            self.sql_sort = " ORDER BY " + self.data_field

    def clear_lb(self):
        """clear the ListBox"""
        self.delete(0, tkinter.END)

    def link(self, widget, link_field):
        """assign a link to child-table"""
        self.linked_table = widget
        self.linked_table.link_field = link_field

    def requery(self, link_value=None):
        """init a cursor to re-setup the ListBox by the link_value"""
        self.link_value = link_value    # store the id, so we know the "master" record we're populated from
        if link_value and self.link_field:
            sql = self.sql_select + " WHERE " + self.link_field + "=?" + self.sql_sort
            print(sql, "| value =", link_value)  # TODO delete this line
            self.cursor.execute(sql, (link_value,))
        else:
            print(self.sql_select + self.sql_sort)  # TODO delete this line
            self.cursor.execute(self.sql_select + self.sql_sort)

        # clear the listbox contents before re-loading
        self.clear_lb()
        for value in self.cursor:
            self.insert(tkinter.END, value[0])
        # if it has the child-table, set that child table to empty
        if self.linked_table:
            self.linked_table.clear_lb()

    def on_select(self, _):

        """execute when one item is selected,
         _ is event, but we don't need it"""
        # notice that when we select the item, then select another item (maybe on the other ListBox)
        # the event now gets triggered and call on_select with no item in self.curselection(),
        # therefore we need to also check it
        if self.linked_table and self.curselection():
            # self is event.widget
            index = self.curselection()[0]
            value = self.get(index),

            # get the artist ID from the database row
            # Make sure we're getting the correct one, by including the link_value if appropriate
            if self.link_value:
                value = value[0], self.link_value
                sql_where = " WHERE " + self.data_field + "=? AND " + self.link_field + "=?"
            else:
                sql_where = " WHERE " + self.data_field + "=?"

            link_id = self.cursor.execute(self.sql_select + sql_where, value).fetchone()[1]
            self.linked_table.requery(link_id)


if __name__ == '__main__':
    conn = sqlite3.connect('music.sqlite')

    mainWindow = tkinter.Tk()
    mainWindow.title('Music DB Browser')
    mainWindow.geometry('1024x768')

    mainWindow.columnconfigure(0, weight=2)
    mainWindow.columnconfigure(1, weight=2)
    mainWindow.columnconfigure(2, weight=2)
    mainWindow.columnconfigure(3, weight=1)  # spacer column on right

    mainWindow.rowconfigure(0, weight=1)
    mainWindow.rowconfigure(1, weight=5)
    mainWindow.rowconfigure(2, weight=5)
    mainWindow.rowconfigure(3, weight=1)

    # ===== labels =====
    tkinter.Label(mainWindow, text="Artists").grid(row=0, column=0)
    tkinter.Label(mainWindow, text="Albums").grid(row=0, column=1)
    tkinter.Label(mainWindow, text="Songs").grid(row=0, column=2)

    # ===== Artists Listbox =====
    artistList = DataListBox(mainWindow, conn, "artists", "name")
    artistList.grid(row=1, column=0, sticky='nsew', rowspan=2, padx=(30, 0))
    artistList.config(border=2, relief='sunken')
    artistList.requery()

    # ===== Albums Listbox =====
    albumLV = tkinter.Variable(mainWindow)
    albumLV.set(("Choose an artist",))
    albumList = DataListBox(mainWindow, conn, "albums", "name", sort_order=("name",))
    albumList.grid(row=1, column=1, sticky='nsew', padx=(30, 0))
    albumList.config(border=2, relief='sunken')
    albumList.requery()
    # albumList.bind('<<ListboxSelect>>', get_songs)
    artistList.link(albumList, "artist")

    # ===== Songs Listbox =====
    songLV = tkinter.Variable(mainWindow)
    songLV.set(("Choose an album",))
    songList = DataListBox(mainWindow, conn, "songs", "title", ("track", "title"))
    songList.requery()
    songList.grid(row=1, column=2, sticky='nsew', padx=(30, 0))
    songList.config(border=2, relief='sunken')
    albumList.link(songList, "album")

    # ===== Main loop =====
    mainWindow.mainloop()
    print("closing database connection")
    conn.close()
