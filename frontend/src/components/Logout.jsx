import React, { Component } from 'react';
import { Redirect } from 'react-router-dom';
import { PropTypes } from 'prop-types';

import AuthService from '../utils/AuthService';
import Spinner from './common/Spinner';

class Logout extends Component {
  static propTypes = {
    loggedIn: PropTypes.bool.isRequired,
    setLoggedIn: PropTypes.func.isRequired,
    displayToast: PropTypes.func.isRequired,
  };

  constructor(props) {
    super(props);
    // TODO: Pass in a configurable API URL
    this.authService = new AuthService();
    this.logout = this.logout.bind(this);
  }

  logout() {
    this.authService
      .logout()
      .then(() => {
        this.props.setLoggedIn(false);
        this.props.displayToast('info', 'You were logged out successfully');
      })
      .catch(error => {
        this.props.displayToast('error', error.message);
      });
  }

  render() {
    if (this.props.loggedIn) {
      this.logout();
      return <Spinner />;
    }
    return <Redirect to="/" />;
  }
}

export default Logout;
