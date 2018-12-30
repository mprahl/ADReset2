import React, { Component } from 'react';
import {
  BrowserRouter, Route, Switch, Redirect,
} from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Navigation from './components/common/Navigation';
import Home from './components/Home';
import Login from './components/Login';
import Logout from './components/Logout';
import SetQuestion from './components/admin/SetQuestion';

import AuthService from './utils/AuthService';
import './App.css';


class App extends Component {
  constructor(props) {
    super(props);
    this.authService = new AuthService();
    if (this.authService.isLoggedIn()) {
      this.state = { loggedIn: true, role: this.authService.getRole() };
    } else {
      this.state = { loggedIn: false, role: null };
    }
    this.setLoggedIn = this.setLoggedIn.bind(this);
    this.displayToast = this.displayToast.bind(this);
    this.ProtectedRoute = this.ProtectedRoute.bind(this);
  }

  setLoggedIn(loggedIn) {
    if (loggedIn) {
      this.setState({ loggedIn: true, role: this.authService.getRole() });
    } else {
      this.setState({ loggedIn: false, role: null });
    }
  }

  // eslint-disable-next-line class-methods-use-this
  displayToast(msgType, msg) {
    toast[msgType](msg);
  }

  ProtectedRoute({ component: ComponentToRender, ...rest }) {
    if (!this.authService.isLoggedIn()) {
      return (
        <Route
          {...rest}
          render={props => (
            <Redirect to={{ pathname: '/login', state: { from: props.location } }} />
          )}
        />
      );
    }

    let authorized = true;
    if (rest.accessRole === 'admin' && this.authService.isAdmin() === false) {
      this.displayToast('error', 'You must be an administrator to access that page');
      authorized = false;
    } else if (rest.accessRole === 'user' && this.authService.isUser() === false) {
      this.displayToast('error', 'You must be an unprivileged user to access that page');
      authorized = false;
    }

    return (
      <Route
        {...rest}
        render={props => (authorized ? (
          <ComponentToRender {...props} />
        ) : (
          <Redirect to={{ pathname: '/' }} />
        ))}
      />
    );
  }

  render() {
    return (
      <BrowserRouter>
        <React.Fragment>
          <Navigation loggedIn={this.state.loggedIn} role={this.state.role} />
          <Switch>
            <Route
              exact
              path="/"
              component={Home}
            />
            <Route
              exact
              path="/login"
              component={() => (
                <Login
                  loggedIn={this.state.loggedIn}
                  setLoggedIn={this.setLoggedIn}
                  displayToast={this.displayToast}
                />)}
            />
            <Route
              exact
              path="/logout"
              component={() => (
                <Logout
                  loggedIn={this.state.loggedIn}
                  setLoggedIn={this.setLoggedIn}
                  displayToast={this.displayToast}
                />)}
            />
            <this.ProtectedRoute
              exact
              path="/configure-questions"
              accessRole="admin"
              component={
                () => <Redirect to={{ pathname: '/configure-questions/1' }} />
              }
            />
            <this.ProtectedRoute
              exact
              path="/configure-questions/:page"
              accessRole="admin"
              component={() => <SetQuestion displayToast={this.displayToast} />}
            />
          </Switch>
          <ToastContainer hideProgressBar={false} />
        </React.Fragment>
      </BrowserRouter>
    );
  }
}

export default App;
