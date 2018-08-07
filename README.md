Proof of concept for creating & running conversations graphs via message / reply model using a simple (ish) UI. 
This is to be considered alpha or pre alpha - code was written swiftly & with minimal testing.


# getting started

You'll want to have PyQt5 installed. You'll also need to add the /conversation/ directory to your PYTHONPATH.


# modules

There are four main submodules
 
 - backend
    Provides Storage interface. Storage backends handle how graphs are saved and loaded from
    some medium. This could be the filesystem, s3, a URL or something else. 
    Also provides a simple Filesystem implementation which saves & loads conversation graph from local disk.
 
 - domain
    Providers repository wide domain models Node & Graph.
    
 - handlers
    Handlers are intended to actually run & keep track of a conversation state. It's intended that you implement your
    own handler to run & store conversation state in your medium. Provides base ConversationHandler to implement 
    and an example in-memory handler.

 - ui
    The UI module provides a PyQt5 GUI for creating, loading & saving conversation graphs (at the moment it supports
    only the default Filesystem storage, but this can be extended).


# scripts

In addition there are two /bin/ scripts 
  - conversation_builder.py
    launches the UI
   
  - tui_conversation.py 
    runs a conversation graph using the in memory handler in a terminal
