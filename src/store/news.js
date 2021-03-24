import * as backend from '@/utils/backend'
import moment from 'moment'

const news_container = {
  module: {
    namespaced: true,

    state: {
      news_url: '',
      news: []
    },
    getters: {
      get_news_url (state) { return state.news_url },
      get_news (state) { return state.news }
    },

    mutations: {
      set_news_url (state, news_url) { state.news_url = news_url },
      set_news (state, news) { state.news = news }
    },

    actions: {
      async request_news (context) {
        let response = await backend.get(context.state.news_url)
        let tmp = []
        for (const news of response.data) {
          let author_response = await backend.get(news['author_url'])
          tmp.push({
            ...news,
            created: moment(news['created']).format(),
            modified: moment(news['modified']).format(),
            author: author_response.data['name']
          })
        }
        console.log('NEWS', tmp)
        context.commit('set_news', tmp)
      }
    }
  }
}

export default news_container
