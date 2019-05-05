import { PropTypes } from 'prop-types';
import React, { Component } from 'react';
import { Card, CardBody, CardHeader, Container } from 'reactstrap';
import { Redirect, withRouter } from 'react-router-dom';

import APIService from '../../utils/APIService';
import Spinner from '../common/Spinner';
import UsernameForm from './UsernameForm';
import './VerifyAnswers.css';
import VerifyAnswersForm from './VerifyAnswersForm';

const cardBodyStlye = {
  backgroundColor: '#ecf0f1',
};

class VerifyAnswers extends Component {
  static propTypes = {
    displayToast: PropTypes.func.isRequired,
    history: PropTypes.object.isRequired,
    loggedIn: PropTypes.bool.isRequired,
    match: PropTypes.object.isRequired,
  };

  constructor(props) {
    super(props);
    this.state = {
      configuredAnswers: [],
      loading: false,
      redirectToHome: false,
    };
    // TODO: Pass in a configurable API URL
    this.apiService = new APIService();
  }

  componentDidMount() {
    const { displayToast, loggedIn } = this.props;
    // There's technically no harm in letting them reset their password when logged in, but
    // there shouldn't be a reason to do that
    if (loggedIn === true) {
      displayToast('error', 'Please log out before resetting your password');
      this.setState({ redirectToHome: true });
      return;
    }
    // If the user has entered in their username, then it will be part of the route
    const { username } = this.props.match.params;
    // Query for the user's configured secret questions
    this.getConfiguredAnswers(username);
  }

  componentDidUpdate(prevProps) {
    // If the username changed, then query the API again
    const { username } = this.props.match.params;
    const oldUsername = prevProps.match.params.username;
    // The most common situation is when oldUsername is null and username is set
    if (username !== oldUsername) {
      this.getConfiguredAnswers(username);
    }
  }

  /**
   * Displays a success message and redirects to the home page when the password is reset.
   */
  onResetSuccess = () => {
    const { displayToast } = this.props;
    displayToast('info', 'Your password was successfully reset');
    this.setState({ redirectToHome: true });
  };

  /**
   * Handles errors from the reset API endpoint.
   *
   * @param {*} error The error that was returned from the reset API endpoint.
   */
  onResetFailure = error => {
    const { displayToast } = this.props;
    displayToast('error', error.message);
    // If the user is locked out, return them to home
    if (error.message.includes('locked')) {
      this.setState({ redirectToHome: true });
    }
  };

  /**
   * Query the API to get the user's configured secret questions.
   */
  getConfiguredAnswers = username => {
    // If the username is null, then there's nothing to do
    if (!username) {
      // Set configuredAnswers to its initial value
      this.setState({ configuredAnswers: [] });
      return;
    }

    this.setState({ configuredAnswers: [], loading: true });
    const { displayToast, history } = this.props;
    this.apiService
      .getUserAnswers(username)
      .then(configuredAnswers => {
        if (configuredAnswers.items.length === 0) {
          displayToast(
            'error',
            'You may not use this feature because you have not previously configured your secret '
              + 'questions',
          );
          history.push('/reset-with-questions/');
        }
        this.setState({ configuredAnswers: configuredAnswers.items, loading: false });
      })
      .catch(error => {
        displayToast('error', error.message);
        this.setState({ loading: false });
      });
  };

  /**
   * Return the JSX of the component to render.
   */
  render() {
    const { configuredAnswers, loading, redirectToHome } = this.state;

    if (redirectToHome) {
      return <Redirect to="/" />;
    }

    let cardContent = null;
    const { username } = this.props.match.params;
    // If the username is null, then ask the user to enter one in a form. If configuredAnswers
    // has a length of 0, then show the form filled in with the username, but disabled while the
    // configured answers are loading.
    if (!username || configuredAnswers.length === 0) {
      cardContent = <UsernameForm baseURL="/reset-with-questions/" disabled={loading} />;
    } else {
      const { displayToast } = this.props;
      cardContent = (
        <VerifyAnswersForm
          configuredAnswers={configuredAnswers}
          displayToast={displayToast}
          onResetFailure={this.onResetFailure}
          onResetSuccess={this.onResetSuccess}
          username={username}
        />
      );
    }

    return (
      <React.Fragment>
        {loading ? <Spinner /> : ''}
        <Container>
          <h2 className="text-center" style={{ marginBottom: '2.5rem' }}>
            Reset Password
          </h2>
          <Card className="custom-card mb-5">
            <CardBody style={cardBodyStlye}>
              This form will allow you to reset your password using the secret questions you defined
              earlier. If you have not done so, you will not be able to use this feature, therefore,
              contact the Help Desk for assistance with your password reset.
            </CardBody>
          </Card>
          <Card className="custom-card">
            <CardHeader>Answer Your Secret Questions</CardHeader>
            <CardBody>{cardContent}</CardBody>
          </Card>
        </Container>
      </React.Fragment>
    );
  }
}

export default withRouter(VerifyAnswers);
