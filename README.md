# Python wrapper for Pushwoosh API

Simple Python 3 wrapper for [Pushwoosh API](https://docs.pushwoosh.com/platform-docs/api-reference/)

NOTE: This is ongoing unofficial project, provided AS IS and supported on best effort basis.


Quick start
-----------

1. Install `pushwoosh_api` package, e.g.:

   ```shell
   pip install git+https://github.com/makcyd/pushwoosh_api.git
   ```

2. Use it as follows:

    ```python
    from pushwoosh_api import Pushwoosh
    
    p = Pushwoosh(api_endpoint="https://cp.pushwoosh.com/json/1.3", api_key="<YOUR KEY HERE>")
    
    message_history = p.get_push_history()
    
    for message in message_history:
        print("[{}] {}".format(message["id"], message["content"]))
    ```
