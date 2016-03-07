import json
import os
import sys
import stripe

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect, HttpResponseNotAllowed
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.files.storage import get_storage_class
from django.views.decorators.csrf import csrf_exempt

from annoying.decorators import render_to
from constantcontact import ConstantContact, Contact
from .forms import KolibriDeploymentForm

class JsonResponse(HttpResponse):
    """Wrapper class for generating a HTTP response with JSON data"""
    def __init__(self, content, *args, **kwargs):
        if not isinstance(content, basestring):
            content = json.dumps(content, ensure_ascii=False)
        super(JsonResponse, self).__init__(content, content_type='application/json', *args, **kwargs)


@render_to("main/map.html")
def map(request): 
    return {"LOCATIONS_JSONP_URL": settings.LOCATIONS_JSONP_URL}


@render_to("main/kickstarter.html")
def kolibri(request):
    """
    summary_info contains the following information:
        collected_funds - total collected
        goal - collection goal
        contributions_count - number of contributors
        latest_contributions - a list of the 4 most recent contributors

    all_contributors contains a list of all contributors

    both latest_contributions and all_contributors items have the following properties:
        by - name of contributor
        created_at - timestamp of donation
        amount - amount of donation (if private, this will be None)
    """
   
    try:
        summary_info = json.load(open(os.path.join(settings.INDIEGOGO_API_DATA_LOCATION, "summary.json"), "r"))
    except IOError:
        summary_info = {
            "collected_funds": None,
            "goal": None,
            "contributions_count": None,
            "latest_contributions": [],
        }
    try:
        all_contributors = json.load(open(os.path.join(settings.INDIEGOGO_API_DATA_LOCATION, "all_contributors.json"), "r"))
    except IOError:
        all_contributors = []

    return {
        "summary_info": json.dumps(summary_info),
        "all_contributors": json.dumps(all_contributors),
    }


@render_to("main/_deploy-form.html")
def kolibriDeployForm(request):
    if request.method == "POST":
        deployment_form = KolibriDeploymentForm(request.POST)
        if deployment_form.is_valid():

            deployment_form.save()

            return HttpResponseRedirect(reverse("map_add_thankyou"))
    else:
        deployment_form = KolibriDeploymentForm()

        
        return {
            'deployment_form': deployment_form,
        }




@csrf_exempt
def cc_indiegogo_signup(request):
    if request.method == "POST":
        constantcontact = ConstantContact(settings.CONSTANT_CONTACT_API_KEY, settings.CONSTANT_CONTACT_ACCESS_TOKEN, settings.CONSTANT_CONTACT_API_URL)
        contact = Contact()
        contact.add_list_id(settings.CONSTANT_CONTACT_LIST_ID)
        contact.set_email_address(request.POST['email'])
        response = constantcontact.post_contacts(contact)

        if response.has_key('error_key'):
            return HttpResponse(response['error_key'])
        else:
            return HttpResponse('201')

def process_donation(request):

    if request.method != "POST":

        return HttpResponseNotAllowed("Only POST is allowed.")

    if not settings.STRIPE_SECRET_API_KEY:

        raise Exception("STRIPE_SECRET_API_KEY must be defined in settings to make payments.")

    data = json.loads(request.body)

    # Set your secret key: remember to change this to your live secret key in production
    # See your keys here https://dashboard.stripe.com/account/apikeys
    stripe.api_key = settings.STRIPE_SECRET_API_KEY

    # Get the credit card details submitted by the form
    token = data["id"]

    metadata = {}
    metadata.update(data)
    metadata.pop("amount", None)
    metadata.pop("email", None)
    metadata.pop("csrfmiddlewaretoken", None)
    metadata.pop("card", None)

    # Create the charge on Stripe's servers - this will charge the user's card
    try:
        charge = stripe.Charge.create(
            amount=data["amount"], # amount in cents, again
            currency=data.get("currency") or "usd",
            source=token,
            metadata=metadata,
        )

        return JsonResponse({"status": "success", "message": "Thank you for your generous donation! We appreciate your support for our mission of promoting equal opportunities for learners around the world!"})

    except Exception, e:

        return JsonResponse({"status": "error", "message": "There was an error processing your donation payment ('%s'). Please try again." % e})


def handler_500(request):
    errortype, value, tb = sys.exc_info()
    context = {
        "errortype": errortype.__name__,
        "value": str(value),
    }
    return HttpResponseServerError(render_to_string("main/500.html", context, context_instance=RequestContext(request)))

def handler_404(request):
    return HttpResponseServerError(render_to_string("main/404.html", {}, context_instance=RequestContext(request)))


@login_required
@csrf_exempt
def file_upload(request):
    if request.method == 'POST':
        storage_class = get_storage_class()()
        file_object = request.FILES.values()[0]
        filename = storage_class.save(None, file_object)
        return HttpResponse(json.dumps({
            "uploaded": 1,
            "fileName": filename,
            "url": settings.MEDIA_URL + "/" + filename,
        }))
