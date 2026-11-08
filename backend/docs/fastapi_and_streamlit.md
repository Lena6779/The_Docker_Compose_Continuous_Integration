FastAPI is a Python web framework for building APIs. It uses type hints and Pydantic models to validate request data automatically and generates interactive documentation at the /docs endpoint.

An endpoint is a URL path combined with an HTTP method, such as GET /health or POST /ask. GET requests read data, while POST requests send data to the server, often to create something or trigger an action.

Streamlit is a Python library for building web interfaces without writing HTML or JavaScript. Widgets like buttons, text inputs, and expanders are created with simple function calls.

Streamlit reruns the entire script from top to bottom every time a user interacts with the page. Session state can be used to remember values between reruns.

In a full-stack app, the Streamlit frontend sends HTTP requests to the FastAPI backend using the requests library, and the backend returns JSON that the frontend displays.
