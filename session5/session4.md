example2.py is a basic example of how to use the MCP server to draw a rectangle in MS Paint.
However the OS that I am working on is MAC, in which we dont have Paint and want Preview to draw a rectangle.
The easiest way I can think of is to open an empty pdf everytime and then draw a rectangle,

You can copy the empty_page.pdf from empty_pdf dir and put it inside preview_results dir whenever you are asked to open a new pdf and draw a rectange over it.

Drawing a rectangle is simple, select the rectangle tool from the markup toolbar and then click and drag to draw a rectangle.(Make Sure this is automated and tranlated in the MCP tools as its done for the Paint application)
Similarly you can add text to the rectangle by selecting the text tool from the markup toolbar and then clicking and dragging to select the text area and then typing the text.

The final result should be a pdf with a rectangle and text inside it

Now create a mcp_server_mac.py file and use example2.py for reference.

Also create a talk2mcp_mac.py to communicate with the mcp_server_mac.py file.


