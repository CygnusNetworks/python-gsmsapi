python-gsmsapi
==============

Python SMS API for some (german) SMS providers

Currently supported providers:

* SMSTrade - http://www.smstrade.de
* Sipgate - http://www.sipgate.de (Sipgate Basic, Plus and Team)

#Examples

```python
import gsmsapi.sipgate_api

username = "foo"
password = "bar
api = gsmsapi.sipgate_api.SipgateAPI(username, password, "team")  # for Sipgate Team accounts
print "Current Sipgate Balance is", api.get_balance()
api.sendsms("49123456789", "Testmessage")

key = "foobar"
api = gsmsapi.smstrade_api.SMSTradeAPI(key, "012345678900", route="gold", debug=False)  # 012345678900 is sender
print "Current SMSTrade Balance is", api.get_balance()
api.send_sms("012345678999", "Testmessage")
```
