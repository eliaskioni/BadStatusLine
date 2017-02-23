# <h1 style="color:#42f448">BadStatusLine</h1>
## Possible bug
>### I thought of creating this project to try to show case a small issue that caused our system to misbehave.

## Disclaimer 
> ### I still consider myself an amateur developer. Kindly forgive my lack of knowledge if what am reporting is wrong, not accurate or irrelevant.

## To reproduce what am saying. 
> ### Clone this repo [BADSTATUSLINE](https://github.com/eliaskioni/BadStatusLine.git) and cd to it's directory. 

***

## It's packaged with docker because I think docker is awesome. 

***

### How to set up

# Step 1

> ## *docker-compose up*

# Step 2 

> ## In a new terminal - 
> ## *docker-compose logs -f worker*

# Step 3

> ## In your browser open this [localhost](http://localhost:8080/api/)

> ## username:password => guest:guest

> ### In the email I have attached an excel file with around 5000 contacts.

> ## upload it. What it will do is read all the contacts in that excel file and initiate sending of SMS to Africa's Talking
> ## In the terminal listening on worker logs check the logs. The exception is been raised randomly. So be patient and wait for it to be raised.
> ## You will see the exception am talking about.

> ## Partly we failed to catch this because it does not show up while sending single SMSes. But sending bulk at once is showed up.

> ### To understand why i think it might affect other people who fail to realise it early. In the lib.AfricasTalkingGateway.py file. Uncomment the send_message function and comment the *send_message* function which we have handled the exception.

> ## You will notice if the BadStatusLine is raised. That thread will fail causing messages not be sent which is something to worry about.

> ## I think we missed to catch it because your doc's in some place mentions that all gateway exceptions will be handled. Which I think is not true.


> # Here are some links for people who bumped into the same issue. 

> # [BADSTATUSLINE](http://stackoverflow.com/questions/1767934/why-am-i-getting-this-error-in-python-httplib)

> # [BADSTATUSLINE](https://github.com/kennethreitz/requests/issues/2364)



