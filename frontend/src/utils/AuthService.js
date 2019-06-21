/* eslint-disable class-methods-use-this */
import decode from 'jwt-decode';
import axios from 'axios';

// TODO: Add a check that runs every x minutes to determine if the token is expired
class AuthService {
  constructor(apiURL) {
    if (apiURL) {
      // Remove the trailing slash if present
      if (apiURL && apiURL.endsWith('/')) {
        this.apiURL = apiURL.slice(0, -1);
      } else {
        this.apiURL = apiURL;
      }
    } else {
      this.apiURL = 'http://127.0.0.1:5000/api/v1';
    }
    this.login = this.login.bind(this);
  }

  login(username, password) {
    const data = { username, password };
    const unexpectedMsg = 'An unexpected error occurred';
    return axios
      .post(`${this.apiURL}/login`, data)
      .then(res => {
        if (res.data && res.data.token) {
          localStorage.setItem('token', res.data.token);
          return;
        }

        throw new Error(unexpectedMsg);
      })
      .catch(error => {
        if (error.response) {
          throw new Error(error.response.data.message);
        }

        throw new Error(unexpectedMsg);
      });
  }

  static isLoggedIn() {
    const token = AuthService.getToken();
    // The double exclamation mark is necessary to convert null to a boolean of false
    return !!token && AuthService.isTokenActive(token);
  }

  static getRole() {
    // This must be called after the user is logged in
    const decoded = decode(AuthService.getToken());
    // Only one role is currently supported
    return decoded.user_claims.roles[0];
  }

  static isAdmin() {
    return AuthService.isLoggedIn() && AuthService.getRole() === 'admin';
  }

  static isUser() {
    return AuthService.isLoggedIn() && AuthService.getRole() === 'user';
  }

  static getUsername() {
    // This must be called after the user is logged in
    const token = AuthService.getToken();
    return decode(token).sub.username;
  }

  static isTokenActive(token) {
    try {
      const decoded = decode(token);
      // https://github.com/auth0/jwt-decode/issues/53
      const expiration = new Date(0);
      expiration.setUTCSeconds(decoded.exp);
      return decoded.exp && expiration.valueOf() > new Date().valueOf();
    } catch (err) {
      return false;
    }
  }

  static setToken(token) {
    localStorage.setItem('token', token);
  }

  static getToken() {
    return localStorage.getItem('token');
  }

  static removeToken() {
    localStorage.removeItem('token');
  }

  static getAuthHeader() {
    return {
      Authorization: `Bearer ${AuthService.getToken()}`,
    };
  }

  apiCall(relativeURL, config = null) {
    return new Promise((resolve, reject) => {
      const axiosConfig = { url: `${this.apiURL}${relativeURL}`, ...config };
      axios(axiosConfig)
        .then(res => {
          resolve(res.data);
        })
        .catch(error => {
          if (error.response && error.response.data) {
            reject(new Error(error.response.data.message));
          } else if (!axios.isCancel(error)) {
            reject(new Error('An unexpected error occurred'));
          }
        });
    });
  }

  authenticatedAPICall(relativeURL, config = null, accessLevel = null) {
    if (!AuthService.isLoggedIn()) {
      return Promise.reject(new Error('You must be logged-in to perform this action'));
    }

    if (accessLevel === 'user' && !AuthService.isUser()) {
      return Promise.reject(new Error('You must be an unprivileged user to perform this action'));
    }
    if (accessLevel === 'admin' && !AuthService.isAdmin()) {
      return Promise.reject(new Error('You must be an administrator to perform this action'));
    }

    const headers = AuthService.getAuthHeader();
    const axiosConfig = { headers, ...config };
    return this.apiCall(relativeURL, axiosConfig);
  }

  logout() {
    if (!AuthService.isLoggedIn) {
      // If the user isn't logged in, then the logout route can't be called, so just remove the
      // token
      AuthService.removeToken();
      return new Promise(resolve => {
        resolve();
      });
    }

    const headers = AuthService.getAuthHeader();

    return axios
      .post(`${this.apiURL}/logout`, {}, { headers })
      .then(() => {
        AuthService.removeToken();
        return true;
      })
      .catch(error => {
        if (error.response) {
          // If the token is expired, then just remove the token from storage
          if (error.response.status === 401) {
            AuthService.removeToken();
            return true;
          }

          throw new Error(error.response.data.message);
        }

        throw new Error('An unexpected error occurred');
      });
  }
}

export default AuthService;
