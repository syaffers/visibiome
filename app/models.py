from django import forms
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User


def upload_path_handler(instance, filename):
    """
    Upload path handler for dynamic naming of folders for user uploads
    :param instance: BiomSearchJob instance of job
    :param filename: String filename
    :return: String the path to file upload for current user
    """
    filename = filename.split('.')
    name, ext = filename[0:-1], filename[-1]
    file_path = \
        settings.MEDIA_ROOT + '{user_id}/{job_id}/{job_id_h}.{ext}'.format(
            user_id=instance.user_id,
            job_id=instance.id,
            job_id_h="{uid}-{id}".format(uid=instance.user_id, id=instance.id),
            ext=ext
        )
    return file_path


class Guest(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)

    def __str__(self):
        if self.status:
            return "{uname} is a guest".format(uname=self.user.username)
        else:
            return "{uname} is not a guest".format(uname=self.user.username)


class EcosystemChoice(models.Model):
    ecosystem = models.CharField(verbose_name="Ecosystem Type", max_length=60)
    ecosystem_proper_name = models.CharField(max_length=60)

    def __str__(self):
        return self.ecosystem_proper_name


class BiomSearchJob(models.Model):
    STOPPED = -1
    VALIDATING = 0
    QUEUED = 1
    PROCESSING = 2
    COMPLETED = 10

    STATUSES = (
        (STOPPED, "Stopped"),
        (QUEUED, "Queued"),
        (VALIDATING, "Validating"),
        (PROCESSING, "Processing"),
        (COMPLETED, "Completed"),
    )

    FILE_IO_ERROR = -1
    NO_ERRORS = 0
    FILE_VALIDATION_ERROR = 1
    SAMPLE_COUNT_ERROR = 2
    DUPLICATE_ID_ERROR = 3
    OTU_NOT_EXIST = 4
    UNKNOWN_ERROR = 5

    ERRORS = (
        (NO_ERRORS, "No errors."),
        (FILE_VALIDATION_ERROR,
         "File/text content has errors. Check JSON/TSV content."),
        (SAMPLE_COUNT_ERROR, "Too many samples, only 1 sample allowed."),
        (DUPLICATE_ID_ERROR, "Duplicate observation IDs."),
        (FILE_IO_ERROR, "Error opening uploaded file. Contact site admin."),
        (OTU_NOT_EXIST,
         "Some OTUs do not exist in the database. Cannot proceed."),
        (UNKNOWN_ERROR,
         "An error occurred. This may be a problem with the system. " +
         "Try again or contact site admin."),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    biom_file = models.FileField(
        upload_to=upload_path_handler, null=True, blank=True
    )
    criteria = models.ManyToManyField(
        'EcosystemChoice', blank=False, max_length=3
    )
    sample_name = models.CharField(
        null=False, max_length=100, default="(no name)"
    )
    status = models.IntegerField(choices=STATUSES, default=VALIDATING)
    error_code = models.IntegerField(choices=ERRORS, default=NO_ERRORS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.pk is None and self.biom_file.name is not None:
            saved_file = self.biom_file
            self.biom_file = None
            super(BiomSearchJob, self).save(*args, **kwargs)
            self.biom_file = saved_file

        super(BiomSearchJob, self).save(*args, **kwargs)

    def __str__(self):
        return "Job by {} created at {}".format(self.user.username,
                                                self.created_at)


class BiomSearchForm(forms.ModelForm):
    """
    The homepage form structure which has a text area, file upload and a set
    of checkboxes for the selection criteria
    """
    class Meta:
        model = BiomSearchJob
        fields = {
            "biom_file": forms.FileField,
            "criteria": forms.MultipleChoiceField(required=True),
        }
        labels = {
            "criteria": "Select the ecosystem(s)",
        }
        widgets = {
            "criteria": forms.CheckboxSelectMultiple,
        }

    biom_file = forms.FileField(
        label="or upload your BIOM file",
        required=False,
    )

    otu_text = forms.CharField(
        label="Paste your OTU table",
        widget=forms.Textarea(attrs={'cols': 30, 'rows': 12}),
    )

    def _empty_otu_text(self, otu_text):
        """
        Checks the validity of the OTU text in the textarea

        :param otu_text: String OTU table in text format
        :return: Boolean truth value of the check
        """
        # if the default string is found, consider it empty
        if otu_text == "Paste OTU table here":
            return True
        # if the box is empty
        if otu_text is None or otu_text == "":
            return True
        # otherwise
        return False

    def clean(self):
        """
        Microbiome search form validation. Checks for chosen criteria and if
        both BIOM and OTU texts are uploaded properly

        :return: Boolean truth value of the check
        """
        # check if OTU table is empty
        try:
            otu_text = self.cleaned_data["otu_text"]
        except KeyError:
            otu_text = None

        # check if criteria is empty
        try:
            criteria = self.cleaned_data["criteria"]
        except KeyError:
            criteria = []

        biom_file = self.cleaned_data["biom_file"]

        # if number of criteria chosen is more than 3
        if len(criteria) > 3:
            msg = forms.ValidationError(
                "Maximum of 3 criteria allowed or all criteria"
            )
            self.add_error("criteria", msg)

        # if number of criteria chosen is 0
        if len(criteria) == 0:
            msg = forms.ValidationError(
                "At least one criteria must be selected"
            )
            self.add_error("criteria", msg)

        # if BIOM file or OTU text is not filled in or submitted
        if self._empty_otu_text(otu_text) and biom_file is None:
            msg = forms.ValidationError(
                "An upload of the OTU table or BIOM file is required"
            )
            self.add_error("biom_file", msg)
            self.add_error("otu_text", msg)

        # if BIOM file and OTU text is both filled in or submitted
        if not self._empty_otu_text(otu_text) and biom_file is not None:
            msg = forms.ValidationError(
                "Only upload the OTU table or BIOM file and not both"
            )
            self.add_error("biom_file", msg)
            self.add_error("otu_text", msg)

        return self.cleaned_data


class UserForm(forms.ModelForm):
    """
    General User form for registration and update details
    """
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "confirm",
        ]
        labels = {
            "email": "Email",
        }
        widgets = {
            "password": forms.PasswordInput,
        }

    confirm = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm Password",
    )

    def clean_confirm(self):
        password = self.cleaned_data.get("password")
        confirm = self.cleaned_data.get("confirm")
        if password and confirm and password != confirm:
            msg = forms.ValidationError("Passwords must match")
            self.add_error("password", msg)
            self.add_error("confirm", msg)
