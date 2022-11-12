# piscale
Connecting a Pi to a kitchen Scale - this allows tracking of your calorie intake based on weight and a database of calorie content for different foods. 

Need to first install the C++ library that the HX711 library relies upon. Repo is here: https://github.com/endail/hx711

Install dependencies via pip3 install - r requirements.txt

After this step, I was still getting the problem below.

ImportError: numpy.core.multiarray failed to import 

I therefore upgraded numpy = "pip3 install -U numpy" and "sudo apt-get install libatlas-base-dev" to resolve that problem. Troubleshooting information was available, here: https://numpy.org/doc/stable/user/troubleshooting-importerror.htm

piscale service enables running piscale as a service via systemd. It will need to be modified to use your own username and loaded as per other services. 