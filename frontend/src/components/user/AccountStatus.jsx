import moment from 'moment';
import { PropTypes } from 'prop-types';
import React, { Component } from 'react';
import { Redirect, withRouter } from 'react-router-dom';
import { Button, Container, Form, Input, Table } from 'reactstrap';

import './AccountStatus.css';
import APIService from '../../utils/APIService';
import Spinner from '../common/Spinner';

class AccountStatus extends Component {
  static propTypes = {
    about: PropTypes.object.isRequired,
    displayToast: PropTypes.func.isRequired,
    history: PropTypes.object.isRequired,
    match: PropTypes.object.isRequired,
  };

  constructor(props) {
    super(props);
    const { match } = this.props;

    this.state = {
      accountStatus: null,
      loading: false,
      username: match.params.username || '',
    };
    // TODO: Pass in a configurable API URL
    this.apiService = new APIService();
    this.getAccountStatus = this.getAccountStatus.bind(this);
    this.getAccountStatusValue = this.getAccountStatusValue.bind(this);
    this.handleUsernameInput = this.handleUsernameInput.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  /**
   * Get the account status when a username is passed in the route when the component mounts.
   */
  componentDidMount() {
    const { username } = this.props.match.params;
    if (username) {
      this.getAccountStatus(username);
    }
  }

  /**
   * Update the account status when a username in the route changes.
   * @param {*} prevProps the previous props before the component updated
   */
  componentDidUpdate(prevProps) {
    const { username } = this.props.match.params;
    const oldUsername = prevProps.match.params.username;
    if (username !== oldUsername) {
      if (!username) {
        // eslint-disable-next-line react/no-did-update-set-state
        this.setState({ accountStatus: null, username: '' });
        return;
      }

      this.getAccountStatus(username);
    }
  }

  /**
   * Gets the Active Directory account status of the user.
   * @param {string} username the username to get the status for
   */
  getAccountStatus(username) {
    this.setState({ accountStatus: null, loading: true, username });

    const { displayToast } = this.props;
    this.apiService
      .getAccountStatus(username)
      .then(accountStatus => this.setState({ accountStatus, loading: false }))
      .catch(error => {
        displayToast('error', error.message);
        this.setState({ loading: false });
      });
  }

  /**
   * Gets the account status value and converts it to a string to display to the user.
   * @param {string} key the key to get
   */
  getAccountStatusValue(key) {
    const { accountStatus } = this.state;
    if (!accountStatus) {
      return '';
    }

    const boolKeys = ['account_is_disabled', 'account_is_locked_out', 'password_never_expires'];
    const timestampKeys = [
      'account_is_unlocked_on',
      'password_can_be_set_on',
      'password_expires_on',
      'password_last_set_on',
    ];

    if (boolKeys.includes(key) === true) {
      return accountStatus[key] === true ? 'Yes' : 'No';
    }

    if (timestampKeys.includes(key) === true) {
      if (accountStatus[key]) {
        const dt = moment.utc(accountStatus[key]);
        if (key !== 'password_last_set_on' && dt <= moment.utc()) {
          return 'Now';
        }

        return dt.local().format('LLL');
      }

      if (key === 'password_expires_on' && accountStatus.password_never_expires === true) {
        return 'Never';
      }

      if (key !== 'password_last_set_on') {
        return 'Now';
      }
    }

    return '';
  }

  /**
   * Update the username in the state based on the form input.
   * @param {*} e the event that updated the form input
   */
  handleUsernameInput(e) {
    this.setState({ username: e.target.value });
  }

  /**
   * Update the account status after the form submission.
   * @param {*} e the form submission event
   */
  handleSubmit(e) {
    e.preventDefault();
    const { username } = this.state;
    const { history, match } = this.props;
    // If the user submitted the form again with the same username, just refresh the data
    if (username === match.params.username) {
      this.getAccountStatus(username);
    } else {
      history.push(`/account-status/${username}`);
    }
  }

  /**
   * Return the JSX of the component to render.
   */
  render() {
    const { about } = this.props;
    if (about.account_status_enabled === false) {
      return <Redirect to="/" />;
    }

    const { loading, username } = this.state;
    return (
      <React.Fragment>
        {loading ? <Spinner /> : ''}
        <Container>
          <h2 className="text-center mb-5">Account Status</h2>
          <Form
            className="mb-5"
            inline
            onSubmit={this.handleSubmit}
            style={{ justifyContent: 'center' }}
          >
            <Input
              className="status-username-input"
              onChange={this.handleUsernameInput}
              placeholder="Enter a username"
              required
              value={username}
            />
            <Button className="status-btn" color="primary" disabled={loading || !username.length}>
              Query
            </Button>
          </Form>
          <Table hover bordered responsive className="secret-questions-table">
            <thead className="thead-blue">
              <tr>
                <th style={{ width: '50%' }}>Attribute</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Account Is Disabled</td>
                <td>{this.getAccountStatusValue('account_is_disabled')}</td>
              </tr>
              <tr>
                <td>Account Is Locked Out</td>
                <td>{this.getAccountStatusValue('account_is_locked_out')}</td>
              </tr>
              <tr>
                <td>When Account Is Unlocked</td>
                <td>{this.getAccountStatusValue('account_is_unlocked_on')}</td>
              </tr>
              <tr>
                <td>When Password Can Be Set</td>
                <td>{this.getAccountStatusValue('password_can_be_set_on')}</td>
              </tr>
              <tr>
                <td>When Password Expires</td>
                <td>{this.getAccountStatusValue('password_expires_on')}</td>
              </tr>
              {/* The height CSS is necessary since if accountStatus is null, then the second
                  column has no text value, which causes it to shrink. */}
              <tr style={{ height: '48px' }}>
                <td>When Password Was Last Set</td>
                <td>{this.getAccountStatusValue('password_last_set_on')}</td>
              </tr>
            </tbody>
          </Table>
        </Container>
      </React.Fragment>
    );
  }
}

export default withRouter(AccountStatus);
