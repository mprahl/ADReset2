import React, { Component } from 'react';
import { Redirect } from 'react-router-dom';
import { PropTypes } from 'prop-types';
import ExitToApp from '@material-ui/icons/ExitToApp';
import Person from '@material-ui/icons/Person';
import Lock from '@material-ui/icons/Lock';
import CircularProgress from '@material-ui/core/CircularProgress';
import 'react-toastify/dist/ReactToastify.css';

import AuthService from './AuthService';
import './Login.css';
import windowsLogo from './windows.png';


class Login extends Component {
  static propTypes = {
    loggedIn: PropTypes.bool.isRequired,
    setLoggedIn: PropTypes.func.isRequired,
    displayToast: PropTypes.func.isRequired,
  }

  constructor(props) {
    super(props);
    this.state = {
      username: '',
      password: '',
      loading: false,
    };

    this.onSubmit = this.onSubmit.bind(this);
    this.handleChange = this.handleChange.bind(this);
    // TODO: Pass in a configurable API URL
    this.authService = new AuthService();
  }

  onSubmit(e) {
    e.preventDefault();
    this.setState({ loading: true });

    this.authService.login(this.state.username, this.state.password)
      .then(() => {
        this.props.setLoggedIn(true);
      })
      .catch((error) => {
        this.setState({ password: '', loading: false });
        this.props.displayToast('error', error.message);
      });
  }

  handleChange(event) {
    this.setState({ [event.target.name]: event.target.value });
  }

  render() {
    if (this.props.loggedIn === true) {
      return (
        <Redirect to="/" />
      );
    }

    return (
      <React.Fragment>
        <div className="container">
          <div className="login-form-wrapper">
            <img className="login-logo" src={windowsLogo} alt="Microsoft Active Directory" />
            <h6 className="form-header">Login with your Windows credentials</h6>
            <form onSubmit={this.onSubmit} className="login-form">
              <div className="form-group">
                <Person className="input-icon" />
                <input
                  onChange={this.handleChange}
                  value={this.state.username}
                  className="form-control login-input"
                  type="text"
                  name="username"
                  required
                  placeholder="Username"
                />
              </div>
              <div className="form-group">
                <Lock className="input-icon" />
                <input
                  onChange={this.handleChange}
                  value={this.state.password}
                  className="form-control login-input"
                  type="password"
                  name="password"
                  required
                  placeholder="Password"
                />
              </div>
              <div className="form-group">
                <button disabled={this.state.loading} className="btn login-btn" type="submit">
                  {
                    this.state.loading
                      ? <CircularProgress className="btn-icon" size="20px" />
                      : <ExitToApp className="btn-icon" />
                  }
                  Login
                </button>
              </div>
            </form>
          </div>
        </div>
      </React.Fragment>
    );
  }
}

export default Login;
