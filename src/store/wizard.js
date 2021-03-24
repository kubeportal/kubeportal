import Vue from 'vue'
import * as backend from '@/utils/backend'

const wizard = {
  module: {
    namespaced: true,

    state: {
      deploymentname: '',
      imagename: '',
      containername: '',
      containerport: '',
      targetport: '',
      serviceport: '',
      namespace: '',
      servicename: '',
      ingressname: '',
      domainname: '',
      subdomain: '',
      hostname_valid: '',
      current_wizard_tab: 'Deployment'
    },

    getters: {
      get_deploymentname (state) { return state.deploymentname },
      get_imagename (state) { return state.imagename },
      get_containername (state) { return state.containername },
      get_containerport (state) { return state.containerport },
      get_serviceport (state) { return state.serviceport },
      get_namespace (state) { return state.namespace },
      get_servicename (state) { return state.servicename },
      get_domainname (state) { return state.domainname },
      get_subdomain (state) { return state.subdomain },
      get_ingressname (state) { return state.ingressname },
      get_hostname_valid (state) { return state.hostname_valid },
      get_current_wizard_tab (state) { return state.current_wizard_tab }
    },

    mutations: {
      set_deployment_name (state, name) { state.deploymentname = name },
      setTargetPort (state, port) { state.targetport = port },
      set_service_port (state, port) { state.serviceport = port },
      set_servicename (state, name) { state.servicename = name },
      set_namespace (state, namespace) { state.namespace = namespace },
      set_ingressname (state, ingressname) { state.ingressname = ingressname },
      set_container_port (state, port) { state.containerport = port },
      set_container_name (state, name) { state.containername = name },
      set_image_name (state, name) { state.imagename = name },
      set_domainname (state, name) { state.domainname = name },
      set_subdomain (state, name) { state.subdomain = name },
      setHostnameValidation (state, valid) { state.validate_hostname = valid },
      set_current_wizard_tab (state, tab) { state.current_wizard_tab = tab }
    },

    actions: {
      async validate_hostname (context, payload) {
        let request_body = { 'hostname' : payload }
        const validation = await backend.post('/check/ingress/', request_body)
        console.log(validation)
        context.commit('setHostnameValidation', validation)
      }
    }
  }
}

export default wizard
