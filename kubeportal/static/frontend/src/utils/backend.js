import axios from 'axios'
import createAuthRefreshInterceptor from 'axios-auth-refresh'
import store from '../store/store.js'
let base_url = process.env['VUE_APP_BASE_URL']
const API_VERSION = 'v2.3.0'

let config = {
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
}

const axiosInstance = axios.create(config)

const refresh_auth_logic = failed_request => {
  let access_token_refresh_url = store.getters['users/get_access_token_refresh_url']
  if (access_token_refresh_url) {
    return post(access_token_refresh_url, { refresh: store.getters['users/get_refresh_token'] }).then(token_refresh_response => {
      store.commit('users/set_access_token', token_refresh_response.data['access'])
      return Promise.resolve()
    })
  }
}

axiosInstance.interceptors.request.use(request => {
  let access_token = store.getters['users/get_access_token']

  request.headers['authorization'] = access_token !== '' ? 'Bearer ' + access_token : undefined
  request.headers['X-CSRFToken'] = store.getters['api/get_csrf_token']
  if (request.url === base_url + '/api/' + API_VERSION + '/' || request.url.includes('/login/')) {
    request.headers['authorization'] = undefined
  }
  // console.log('HEADER', request.headers)
  return request
})

createAuthRefreshInterceptor(axiosInstance, refresh_auth_logic)

export async function get (absolute_url, options = {}) {
  try {
    if (absolute_url === '') {
      let response = await axiosInstance.get(base_url + '/api/' + API_VERSION + '/', options)
      // console.log('GET ' + absolute_url, response)
      return response
    }
    let response = await axiosInstance.get(absolute_url, options)
    // console.log('GET' + absolute_url, response)
    return response
  } catch {
    return undefined
  }
}

export async function post (absolute_url, payload) {
  try {
    let response = await axiosInstance.post(absolute_url, payload)
    // console.log('POST ' + absolute_url, response)
    return response
  } catch {
    return undefined
  }
}

export async function patch (absolute_url, payload) {
  try {
    let response = await axiosInstance.patch(absolute_url, payload)
    // console.log('PATCH ' + absolute_url, response)
    return response
  } catch {
    return undefined
  }
}

/*
export async function get2 (absolute_url) {
  try {
    if (absolute_url === '') {
      let response = await axiosInstance.get(base_url + '/api/' + API_VERSION + '/')
      return response
    }
    let response = await axiosInstance.get(absolute_url, {
      responseType: 'blob'
    })
    return response
  } catch {
    return undefined
  }
}
  */
