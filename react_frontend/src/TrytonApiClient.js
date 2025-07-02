export default class TrytonApiClient {
  constructor(onError) {
    this.onError = onError;
  }

  async request(options) {
    let response = await this.requestInternal(options);
    if (response.status === 401 && options.url !== '/web-user-tokens') {
      const refreshResponse = await this.put('/web-user-tokens', {
        access_token: localStorage.getItem('accessToken'),
      });
      if (refreshResponse.ok) {
        localStorage.setItem('accessToken', refreshResponse.body.access_token);
        response = await this.requestInternal(options);
      }
    }
    if (response.status >= 500 && this.onError) {
      this.onError(response);
    }
    return response;
  }

  async requestInternal(options) {
    let query = new URLSearchParams(options.query || {}).toString();
    if (query !== '') {
      query = '?' + query;
    }

    let response;
    let url = options.server;
    if (options.database !== undefined){
      url = options.server + '/' + options.database;
    }
    url = url + options.url;

    try {
      response = await fetch(url + query, {
        method: options.method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem('accessToken'),
          ...options.headers,
        },
	//credentials: options.url === '/web-user-tokens' ? 'include' : 'omit',
        body: options.body ? JSON.stringify(options.body) : null,
      });
    }
    catch (error) {
      response = {
        ok: false,
        status: 500,
        json: async () => { return {
          code: 500,
          message: 'The server is unresponsive',
          description: error.toString(),
        }; }
      };
    }

    let message
    if (response.status >= 400){
      try {
        message = await response.text()
      }
      catch{
        message = 'Unespected error ocurred. Retry later. (' + response.status + ')'
      }
    }
    else {
      message = response.status !== 204 ? await response.json() : null
    }

    if (response.status >= 400){
      return {
        ok: false,
        status: response.status,
	body: message
      };
    }
    else {
      return {
        ok: response.ok,
        status: response.status,
	body: message
      };
    }
  }

  async get(server, database, url, query, options) {
    return this.request({method: 'GET', server, database, url, query, ...options});
  }

  async post(server, database, url, body, options) {
    return this.request({method: 'POST', server, database, url, body, ...options});
  }

  async put(server, database, url, body, options) {
    return this.request({method: 'PUT', server, database, url, body, ...options});
  }

  async delete(server, database, url, options) {
    return this.request({method: 'DELETE', server, database, url, ...options});
  }

  async login(username, password, server, database) {
    const response = await this.post(server, database, '/web-user-tokens', {}, {
      headers: {
        Authorization:  'Basic ' + btoa(username + ":" + password)
      }
    });
    if (!response.ok) {
      return response.status === 401 ? 'fail' : 'error';
    }
    localStorage.setItem('accessToken', response.body.access_token);
    return 'ok';
  }

  async logout(server, database) {
    await this.delete(server, database, '/web-user-tokens');
    localStorage.removeItem('accessToken');
  }

  isAuthenticated() {
    return localStorage.getItem('accessToken') !== null;
  }
}
