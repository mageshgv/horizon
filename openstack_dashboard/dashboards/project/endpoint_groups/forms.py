#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# @author: Ronak Shah

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from django import http
from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class UpdateEPG(forms.SelfHandlingForm):
    name = forms.CharField(max_length=80, label=_("Name"), required=False)
    description = forms.CharField(max_length=80, label=_("Description"), required=False)
    #l2_policy_id = forms.ChoiceField(label=_("L2 Policy"), required=False)
    failure_url = 'horizon:project:endpoint_groups:index'

    def __init__(self, request, *args, **kwargs):
        super(UpdateEPG, self).__init__(request, *args, **kwargs)
        #l2_pol_id = api.group_policy.l2policy_list(request, tenant_id=tenant_id)

    def handle(self, request, context):
        epg_id = self.initial['epg_id']
        name_or_id = context.get('name') or epg_id
        try:
            epg = api.group_policy.epg_update(request, epg_id, **context)
            msg = _('EPG %s was successfully updated.') % name_or_id
            LOG.debug(msg)
            messages.success(request, msg)
            return epg
        except Exception as e:
            msg = _('Failed to update EPG %(name)s: %(reason)s' %
                    {'name': name_or_id, 'reason': e})
            LOG.error(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)


class CreateContractForm(forms.SelfHandlingForm):
    #This function does Add Provided contracts to EPG
    contract = forms.MultipleChoiceField(label=_("Provided Contracts"),)
    
    def __init__(self, request, *args, **kwargs):
        super(CreateContractForm, self).__init__(request, *args, **kwargs)
        contracts = []
        try:
            tenant_id = self.request.user.tenant_id
            epg_id = kwargs['initial']['epg_id']
            epg = api.group_policy.epg_get(request, epg_id)
            providedcontracts = epg.get("provided_contracts") 
            items = api.group_policy.contract_list(request, tenant_id=tenant_id)
            contracts = [(p.id,p.name) for p in items if p.id not in providedcontracts]
        except Exception as e:
            pass
        self.fields['contract'].choices = contracts
    
    def handle(self,request,context):
        epg_id = self.initial['epg_id']
        epg = api.group_policy.epg_get(request, epg_id)
        url = reverse("horizon:project:endpoint_groups:epgdetails", kwargs={'epg_id': epg_id})
        try:
            for contract in epg.get("provided_contracts"):
                context['contract'].append(contract)
            contracts = dict([(item,'string') for item in context['contract']])
            api.group_policy.epg_update(request,epg_id,provided_contracts=contracts)
            msg = _('Contract added successfully!')
            messages.success(request, msg)
            LOG.debug(msg)
            return http.HttpResponseRedirect(url)
        except Exception:
            msg = _('Failed to add contract!')
            redirect = reverse("horizon:project:endpoint_groups:epgdetails", kwargs={'epg_id': epg_id})
            LOG.error(msg)
            exceptions.handle(request, msg, redirect=redirect)

class RemoveContractForm(forms.SelfHandlingForm):
    contract = forms.MultipleChoiceField(label=_("Provided Contracts"),)
    
    def __init__(self, request, *args, **kwargs):
        super(RemoveContractForm, self).__init__(request, *args, **kwargs)
        contracts = []
        try:
            tenant_id = self.request.user.tenant_id
            epg_id = kwargs['initial']['epg_id']
            epg = api.group_policy.epg_get(request, epg_id)
            providedcontracts = epg.get("provided_contracts") 
            items = api.group_policy.contract_list(request, tenant_id=tenant_id)
            contracts = [(p.id,p.name) for p in items if p.id in providedcontracts] 
        except Exception as e:
            pass
        self.fields['contract'].choices = contracts
    
    def handle(self,request,context):
        epg_id = self.initial['epg_id']
        url = reverse("horizon:project:endpoint_groups:epgdetails", kwargs={'epg_id': epg_id})
        try:
            epg = api.group_policy.epg_get(request, epg_id)
            old_contracts = epg.get("provided_contracts")
            for contract in context['contract']:
                old_contracts.remove(contract)
            contracts = dict([(item,'string') for item in old_contracts])
            api.group_policy.epg_update(request,epg_id,provided_contracts=contracts)
            msg = _('Contract removed successfully!')
            messages.success(request, msg)
            LOG.debug(msg)
            return http.HttpResponseRedirect(url)
        except Exception:
            msg = _('Failed to remove contract!')
            redirect = reverse("horizon:project:endpoint_groups:epgdetails", kwargs={'epg_id': epg_id})
            LOG.error(msg) 
            exceptions.handle(request, msg, redirect=redirect)

class AddConsumedForm(forms.SelfHandlingForm):
    contract = forms.MultipleChoiceField(label=_("Consumed Contracts"),)
    
    def __init__(self, request, *args, **kwargs):
        super(AddConsumedForm, self).__init__(request, *args, **kwargs)
        contracts = []
        try:
            tenant_id = self.request.user.tenant_id
            epg_id = kwargs['initial']['epg_id']
            epg = api.group_policy.epg_get(request, epg_id)
            consumedcontracts = epg.get("consumed_contracts")             
            items = api.group_policy.contract_list(request, tenant_id=tenant_id)
            contracts = [(p.id,p.name) for p in items if p.id not in consumedcontracts]
        except Exception as e:
            pass
        self.fields['contract'].choices = contracts
    
    def handle(self,request,context):
        epg_id = self.initial['epg_id']
        url = reverse("horizon:project:endpoint_groups:epgdetails", kwargs={'epg_id': epg_id})
        try:
            epg = api.group_policy.epg_get(request, epg_id)
            for contract in epg.get("consumed_contracts"):
                context['contract'].append(contract)
            consumed = dict([(item,'string') for item in context['contract']])
            api.group_policy.epg_update(request,epg_id,consumed_contracts=consumed)
            msg = _('Contract Added successfully!')
            messages.success(request, msg)
            LOG.debug(msg)
            return http.HttpResponseRedirect(url)
        except Exception:
            msg = _('Failed to add contract!')
            redirect = reverse("horizon:project:endpoint_groups:epgdetails", kwargs={'epg_id': epg_id})
            LOG.error(msg)  
            exceptions.handle(request, msg, redirect=redirect)

class RemoveConsumedForm(forms.SelfHandlingForm):
    contract = forms.MultipleChoiceField(label=_("Consumed Contracts"),)
    
    def __init__(self, request, *args, **kwargs):
        super(RemoveConsumedForm, self).__init__(request, *args, **kwargs)
        contracts = []
        try:
            tenant_id = self.request.user.tenant_id
            epg_id = kwargs['initial']['epg_id']
            epg = api.group_policy.epg_get(request, epg_id)
            consumedcontracts = epg.get("consumed_contracts") 
            items = api.group_policy.contract_list(request, tenant_id=tenant_id)
            contracts = [(p.id,p.name) for p in items if p.id in consumedcontracts]
        except Exception as e:
            pass
        self.fields['contract'].choices = contracts
    
    def handle(self,request,context):
        epg_id = self.initial['epg_id']
        url = reverse("horizon:project:endpoint_groups:epgdetails", kwargs={'epg_id': epg_id})
        try:
            epg = api.group_policy.epg_get(request, epg_id)
            old_contracts = epg.get("consumed_contracts")
            for contract in context['contract']:
                old_contracts.remove(contract)
            consumed = dict([(item,'string') for item in old_contracts])
            api.group_policy.epg_update(request,epg_id,consumed_contracts=consumed)
            msg = _('Contract removed successfully!')
            messages.success(request, msg)
            LOG.debug(msg)
            return http.HttpResponseRedirect(url)
        except Exception:
            msg = _('Failed to remove contract!')
            redirect = url
            LOG.error(msg)   
            exceptions.handle(request, msg, redirect=redirect)
