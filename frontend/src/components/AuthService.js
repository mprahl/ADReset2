/* eslint-disable class-methods-use-this */
import decode from 'jwt-decode';
import axios from 'axios';


// TODO: Add a check that runs every x minutes to determine if the token is expired
class AuthService {
  constructor(apiURL) {
    this.apiURL = apiURL || 'http://127.0.0.1:5000/api/v1/';
    this.login = this.login.bind(this);
  }

  login(username, password) {
    const data = { username, password };
    const unexpectedMsg = 'An unexpected error occurred';
    return axios.post(`${this.apiURL}login`, data)
      .then((res) => {
        if (res.data && res.data.token) {
          localStorage.setItem('token', res.data.token);
          return;
        }

        throw new Error(unexpectedMsg);
      })
      .catch((error) => {
        if (error.response) {
          throw new Error(error.response.data.message);
        }

        throw new Error(unexpectedMsg);
      });
  }

  isLoggedIn() {
    const token = this.getToken();
    // The double exclamation mark is necessary to convert null to a boolean of false
    return !!token && this.isTokenActive(token);
  }

  getRole() {
    // This must be called after the user is logged in
    const decoded = decode(this.getToken());
    // Only one role is currently supported
    return decoded.user_claims.roles[0];
  }

  isTokenActive(token) {
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

  setToken(token) {
    localStorage.setItem('token', token);
  }

  getToken() {
    return localStorage.getItem('token');
  }

  removeToken() {
    localStorage.removeItem('token');
  }

  logout() {
    if (!this.isLoggedIn) {
      // If the user isn't logged in, then the logout route can't be called, so just remove the
      // token
      this.removeToken();
      return new Promise((resolve) => { resolve(); });
    }

    const headers = {
      Authorization: `Bearer ${this.getToken()}`,
    };

    return axios.post(`${this.apiURL}logout`, {}, { headers })
      .then(() => {
        this.removeToken();
        return true;
      })
      .catch((error) => {
        if (error.response) {
          // If the token is expired, then just remove the token from storage
          if (error.response.status === 401) {
            this.removeToken();
            return true;
          }

          throw new Error(error.response.data.message);
        }

        throw new Error('An unexpected error occurred');
      });
  }
}


export default AuthService;
