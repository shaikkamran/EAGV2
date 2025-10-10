
talk2mcp.py gets a FinalAnswer and when its run we are calling a bunch of tools post obtaining the final answer so that the loop calls functions that can draw a rectange and embed text inside it.

All the functionalities are working fine, but I want my agent only to be able to draw a rectangle and embed text inside it.
Hence Modify the prompt accordingly so that the agent only calls the functions that can draw a rectangle and embed text inside it once it obtains the 
Final Answer. Also Make sure the agent selects the right and reasonable rectange co-ordinates.

Make Sure this happens in a separate file called talk2mcp_agent.py wherein all the code is remained same but the prompt addition needs to happen as described 
so that the agent has some more autonomy