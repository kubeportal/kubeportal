<template>
  <div>
  <div>
    <v-row justify="space-between" align="center" no-gutters class="white">
      <v-col cols="2">
        <v-btn
          icon
          @click="show_menu = !show_menu"
          x-large
        >
          <v-icon>mdi-menu</v-icon>
        </v-btn>
      </v-col>
      <v-col cols="2">
        <div class="live-refresh-container">
        <v-switch
          v-model="live_refresh"
          label="live refresh"
        ></v-switch>
        <v-progress-circular
          v-if="live_refresh && !refresh_loading"
          size="20"
          color="primary"
          value="0"
          class="progress-spinner"
        />
        <v-progress-circular
          v-if="live_refresh && refresh_loading"
          size="20"
          color="primary"
          indeterminate
          class="progress-spinner"
        />
        </div>
      </v-col>
      <v-col cols="2">
        <span class="total">
          {{ total }}
        </span>
        <v-tooltip bottom v-if="more_than_tenthousand">
          <template v-slot:activator="{ on, attrs }">
            <v-icon color="orange" v-bind="attrs" v-on="on"> mdi-alert </v-icon>
          </template>
          <span> Only a maximum of 10000 log entries can be displayed. To access all entries, please download them as a zip. </span>
        </v-tooltip>
      </v-col>
      <v-col class="download" @click="download" cols="1">
        <v-tooltip bottom>
          <template v-slot:activator="{ on, attrs }">
            <v-btn type="button" icon v-bind="attrs" x-large v-on="on">
              <v-icon> mdi-download </v-icon>
            </v-btn>
          </template>
          <span>download {{new Date().toISOString()}}-{{this.pod.name}}-logs.txt</span>
        </v-tooltip>
      </v-col>
    </v-row>
    <v-card v-if="show_menu" class="menu" outlined raised>
      <v-row justify="space-between" align="center">

        <v-col cols="6">
          <v-form @submit="search_submit">
            <v-text-field
              v-model="search_logs"
              label="Search"
              append-outer-icon="mdi-close"
              @click:append-outer="search_logs = ''"
            ></v-text-field>
          </v-form>
        </v-col>
        <v-col cols="2" v-if="search_logs !== ''">
          <v-btn
            icon
            @click="next_log('previous')"
            x-large
          >
            <v-icon>mdi-arrow-left</v-icon>
          </v-btn>
          <v-btn
            icon
            @click="next_log('next')"
            x-large
          >
            <v-icon>mdi-arrow-right</v-icon>
          </v-btn>
        </v-col>
        <v-col cols="2" v-if="search_logs !== ''">
          <div class="occurances">
             {{ current_idx + 1 }} of {{ search_indexe.length }}
          </div>
        </v-col>
        <v-col cols="2">
          <v-tooltip bottom>
            <template v-slot:activator="{ on, attrs }">
              <v-btn type="button" icon v-bind="attrs" x-large v-on="on" @click="jump('up')">
                <v-icon> mdi-chevron-double-up </v-icon>
              </v-btn>
            </template>
            <span>Jump to top</span>
          </v-tooltip>
          <v-tooltip bottom>
            <template v-slot:activator="{ on, attrs }">
              <v-btn type="button" icon v-bind="attrs" x-large v-on="on" @click="jump('down')">
                <v-icon> mdi-chevron-double-down </v-icon>
              </v-btn>
            </template>
            <span>Jump to bottom</span>
          </v-tooltip>
        </v-col>
      </v-row>
      <v-row >
        <v-col cols="2">
          <v-text-field
           label="refresh rate"
           type="number"
           v-model="refresh_rate"
           suffix="ms"
           :rules="[rules.refresh_rate]"
          />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2">
          <RequestSpinner v-if="is_zip_loading" />
          <div v-if="!is_zip_loading">
            <v-tooltip bottom>
              <template v-slot:activator="{ on, attrs }">
                <v-btn
                  @click="download_zip_logs"
                  v-bind="attrs" v-on="on"
                >
                  download all logs as zip <v-icon> mdi-download </v-icon>
                </v-btn>
              </template>
              <span> Download all logs as a zip file. Fetching and zipping the logs may take up to a couple of minutes depending on the amount of log entries.</span>
            </v-tooltip>
          </div>
        </v-col>
      </v-row>
    </v-card>
  </div>
  <div @scroll="is_in_view" class="logs" ref="logs">

    <div ref="scrollblock" :class="is_loading ? 'invisible' : 'scrollblock'"> </div>
    <div class="endoflogs" v-if="end_of_logs" > ... </div>
    <RequestSpinner v-if="is_loading && !end_of_logs" />
    <div class="logfiller">
      <div v-for="(log, index) in logs"
        :key="index"
        :id="'log_entry_' + index"
      >
        <p v-if="log.stream == 'stderr'" class="stderr">
          {{ log.log }}
        </p>
        <p v-else class="stdout">
          {{ log.log }}
        </p>
      </div>
      </div>
    </div>

  </div>
</template>

<script>

import RequestSpinner from '@/components/RequestSpinner'
export default {
  name: 'Logs',
  components: { RequestSpinner },
  props: ['pod', 'namespace'],
  data () {
    return {
      is_loading: false,
      end_of_logs: false,
      search_logs: '',
      search_indexe: [],
      current_idx: 0,
      prev_idx: undefined,
      show_menu: false,
      live_refresh: false,
      refresh_rate: 1000,
      interval_id: undefined,
      rules: {
        refresh_rate: value => value > 499 || 'refresh rate has to be atleast 500ms'
      },
      logs: [],
      page_number: 0,
      total: '',
      refresh_loading: false,
      more_than_tenthousand: false,
      is_zip_loading: false
    }
  },
  watch: {
    refresh_rate () {
      if (this.refresh_rate > 499 && this.live_refresh) {
        if (this.interval_id) clearInterval(this.interval_id)
        this.set_refresh()
      }
    },
    live_refresh (value) {
      if (value) {
        this.set_refresh()
      } else {
        clearInterval(this.interval_id)
      }
    },
    search_logs (value) {
      if (this.prev_idx) {
        let elem = document.getElementById('log_entry_' + this.prev_idx)
        elem.classList.remove('focused')
      }
      if (value !== '') {
        this.current_idx = 0
        let indexe = []
        let idx = 0
        for (const entry of this.logs) {
          if (entry.log.toLowerCase().indexOf(value.toLowerCase()) !== -1) {
            indexe.push(idx)
          }
          idx++
        }
        this.search_indexe = indexe
      }
    },
    logs (new_value, old_value) {
      if (old_value && new_value.length === old_value.length) {
        this.end_of_logs = true
      } else if (this.live_refresh) {
        this.$refs.logs.scrollTop = this.$refs.logs.scrollHeight + 1000
      }else {
        this.$refs.logs.scrollTop = 2200
        this.is_loading = false
      }
    }
  },
  methods: {
    search_submit (e) {
      e.preventDefault()
      this.next_log('next')
    },
    set_refresh () {
      if (this.refresh_rate > 499) {
        this.interval_id = setInterval(async () => {
          this.refresh_loading = true
          const [result, _] = await this.$store.dispatch('pods/request_logs', {
            namespace: this.namespace,
            pod_name: this.pod.name,
            logs_url: this.pod.logs_url,
            page_number: 0
          })
          const is_same_log = (a, b) => a._id === b._id
          const compare_logs = (left, right, compare_function) =>
            left.filter(left_value =>
              !right.some(right_value =>
                compare_function(left_value, right_value)))

          let new_logs = compare_logs(result, this.logs, is_same_log)
          this.logs = [...this.logs, ...new_logs]
          this.refresh_loading = false
        }, this.refresh_rate)
      }
    },
    jump (direction) {
      if (direction === 'up') {
        this.$refs.logs.scrollTop = 0
      } else {
        this.$refs.logs.scrollTop = this.$refs.logs.scrollHeight
      }
    },
    next_log (direction) {
      if (this.prev_idx) {
        let elem = document.getElementById('log_entry_' + this.prev_idx)
        elem.classList.remove('focused')
      }

      if (direction === 'next' && this.current_idx < this.search_indexe.length - 1) {
        this.current_idx = this.current_idx + 1
      } else if (direction === 'next') {
        this.current_idx = 0
      } else if (direction === 'previous' && this.current_idx > 0) {
        this.current_idx = this.current_idx - 1
      } else {
        this.current_idx = this.search_indexe.length - 1
      }

      let idx = this.search_indexe[this.current_idx]
      let elem = document.getElementById('log_entry_' + idx)
      let elem_rect = elem.getBoundingClientRect()
      elem.classList.add('focused')
      this.$refs.logs.scrollTop = this.$refs.logs.scrollTop + elem_rect.top - 300

      this.prev_idx = idx
    },
    download () {
      if (!this.logs) return
      const combinded_logs = this.logs.map(log => log.log).join('\n')
      const element = document.createElement('a')
      element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(combinded_logs))
      element.setAttribute('download', `${new Date().toISOString()}-${this.pod.name}-logs.txt`)
      element.style.display = 'none'
      document.body.appendChild(element)
      element.click()
      document.body.removeChild(element)
    },
    is_in_view () {
      const rect = this.$refs.scrollblock.getBoundingClientRect()
      const elem_top = rect.top
      const elem_bottom = rect.bottom
      const is_visible = (elem_top >= 0) && (elem_bottom <= window.innerHeight)
      if (!this.is_loading && is_visible) {
        this.request_logs()
      }
    },
    async download_zip_logs () {
      this.is_zip_loading = true
      await this.$store.dispatch('pods/request_zip_logs_download', {
        logs_url: this.pod.logs_url,
        file_name: `${new Date().toISOString()}-${this.pod.name}-logs.zip`
      })
      this.is_zip_loading = false
    },
    async request_logs () {
      this.is_loading = true
      const [result, total] = await this.$store.dispatch('pods/request_logs', {
        namespace: this.namespace,
        pod_name: this.pod.name,
        logs_url: this.pod.logs_url,
        page_number: this.page_number
      })
      this.logs = [...result, ...this.logs]
      this.page_number = this.page_number + 1
      if (total['relation'] === 'eq') {
        this.total = `Found ${total['value']} entries`
      } else if (total['relation'] === 'gte') {
        if (total['value'] === 10000) {
          this.more_than_tenthousand = true
        }
        this.total = `Found more than ${total['value']} entries`
      }
    }
  },
  mounted () {
    this.request_logs()
  }
}
</script>

<style scoped>
.scrollblock {
  opacity: 0;
  background-color: red;
  width: 100%;
  height: 10em;
}
.invisible {
  display: none;
}
.logs {
  width: 100%;
  height: 60vh;
  overflow-y: scroll;
  background-color: black;
  position: relative;
  opacity: 0.85;
}
.download {
  color: white;
}
.stderr {
  color: red;
  margin: 0;
}
.stdout {
  color: white;
  margin: 0;
}
.logfiller {
 width: 100%;
 height: 100%;
}
.endoflogs {
  display: block;
  text-align: center;
  color: white;
}
.focused {
  background-color: rgba(255, 255, 255, .3);
  padding-bottom: 5px;
  padding-top: 5px;
}
.occurances {
  text-align: center;
  padding-top: 10%;
}
.menu {
  padding: 0 1em;
  position: absolute;
  z-index: 1000;
  width: 60%;
  right: 0.5%;
  text-align: center;
}
.live-refresh-container {
  display: flex;
  justify-content: center;
  align-items: center;
}
.progress-spinner {
  margin: 0 1em;
}
.total {
 text-align: center;
}
</style>
