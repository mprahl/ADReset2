import React, { Component } from 'react';
import { BrowserRouter, Route, Switch } from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Navigation from './components/Navigation';
import Home from './components/Home';
import Login from './components/Login';
import Logout from './components/Logout';

import AuthService from './components/AuthService';
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

  render() {
    return (
      <BrowserRouter>
        <React.Fragment>
          <Navigation loggedIn={this.state.loggedIn} role={this.state.role} />
          <Switch>
            <Route
              exact
              path="/"
              component={() => (
                <Home displayToast={this.displayToast} />
              )}
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
          </Switch>
          <ToastContainer hideProgressBar={false} />
        </React.Fragment>
      </BrowserRouter>
    );
  }
}

export default App;
