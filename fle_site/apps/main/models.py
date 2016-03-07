from django.db import models

# Create your models here.
class KolibriDeployment(models.Model):
    # Required fields
    
    contact_name = models.CharField(max_length=100)
    contact_email = models.EmailField(max_length=254)
    deployment_city = models.CharField(max_length=75, help_text='The city, town, or district where Kolibri is being used')
    deployment_country = models.CharField(max_length=75)
    description = models.TextField(help_text='In 2-5 sentences, tell us about this deployment.')

    # optional bonus fields
    organization_name = models.CharField(max_length=150, blank=True, help_text='The organization who is implementing this project, if any.')
    organization_url = models.URLField(blank=True)
    num_students = models.CharField(max_length=20, blank=True, verbose_name=u'Number of students', help_text='Total number of students using Kolibri through this deployment.')
    student_age_range = models.CharField(max_length=75, blank=True, verbose_name=u'Age range of students', help_text='The range of ages of students participating in the deployment.')
    num_kolibri_devices = models.IntegerField(blank=True, null=True, verbose_name=u'Number of Kolibri devices', help_text='The number of computers where Kolibri has been installed. E.g. 3 Raspberry Pis')
    server_os = models.CharField(max_length=75, blank=True, verbose_name=u'Operating System(s)', help_text='E.g. Windows, Linux, Mac, or Raspbian')
    hardware_setup = models.CharField(max_length=100, blank=True, help_text='E.g. 2 RPi running local WiFi content servers.')

    def __str__(self):
        return self.title

    def clean(self):
        """Ensure that organization city and country are supplied together or not at all"""
        cleaned_data = super(DeploymentStory, self).clean()
        if (self.organization_city or self.organization_country) and not (self.organization_city and self.organization_country):
            raise ValidationError("If you supply an organization city, you must supply the organization_country, and vice versa")
        # Enforce an org name if URL is provided (but not vice versa b/c some orgs may not have websites)
        if self.organization_url and not self.organization_name:
            raise ValidationError("You must provide an organization name if the organization has a website!")
        return cleaned_data

    def linked_org_name(self):
        """Return HTML anchored org name if URL exists, otherwise just org name"""
        if self.organization_url:
            return "<a href='%(url)s'>%(org_name)s</a>" % {'url': self.organization_url, 'org_name': self.organization_name}
        elif self.organization_name:
            return self.organization_name
        else:
            return False
        
    def deployment_location(self):
        return "%(city)s, %(country)s" % {'city': self.deployment_city, 'country': self.deployment_country}

    def organization_location(self):
        if self.organization_city:
            return "%(city)s, %(country)s" % {'city': self.organization_city, 'country': self.organization_country} 
        else:
            return False
