import PropTypes from 'prop-types';
import React, { Component } from 'react';
import { Button, Form, FormGroup, Label } from 'reactstrap';

import APIService from '../../utils/APIService';
import PasswordInput from '../common/PasswordInput';

class VerifyAnswersForm extends Component {
  static propTypes = {
    configuredAnswers: PropTypes.array.isRequired,
    displayToast: PropTypes.func.isRequired,
    onResetFailure: PropTypes.func.isRequired,
    onResetSuccess: PropTypes.func.isRequired,
    username: PropTypes.string.isRequired,
  };

  constructor(props) {
    super(props);
    const { configuredAnswers } = this.props;
    const answers = [];
    for (let i = 0; i < configuredAnswers.length; i += 1) {
      answers[i] = '';
    }
    this.state = {
      answers,
      loading: false,
      newPassword: '',
      newPasswordDisabled: true,
      newPasswordRepeat: '',
    };
    // TODO: Pass in a configurable API URL
    this.apiService = new APIService();
  }

  /**
   * Handles when the text box for an answer changes.
   *
   * @param {*} e The event that triggered this method.
   */
  handleAnswerChange = e => {
    const { value } = e.target;
    const answerID = e.target.attributes['data-id'].value;
    // Store the answer in the state
    this.setState(oldState => {
      const answers = oldState.answers.slice();
      answers[answerID] = value;
      // Only enable the new password text boxes once every secret question is answered. This
      // provides a hint to the user that they must fill in their answers first.
      const newPasswordDisabled = !answers.every(answer => !!answer);
      return { answers, newPasswordDisabled };
    });
  };

  /**
   * Handles when the value of an input changes.
   *
   * @param {*} e The event that triggered this method.
   */
  handleInputChange = e => {
    const { name, value } = e.target;
    this.setState({ [name]: value });
  };

  /**
   * Handles when the form is submitted and triggers a password reset.
   *
   * @param {*} e The event that triggered this method.
   */
  handleResetSubmit = e => {
    e.preventDefault();
    const {
      configuredAnswers,
      displayToast,
      onResetFailure,
      onResetSuccess,
      username,
    } = this.props;
    const { answers, newPassword, newPasswordRepeat } = this.state;

    if (newPassword !== newPasswordRepeat) {
      displayToast('error', 'The provided new passwords do not match. Please try again.');
      return;
    }

    // Set the secret answers in the format the reset API endpoint expects
    const apiAnswers = [];
    configuredAnswers.forEach((configuredAnswer, index) => {
      apiAnswers.push({
        question_id: configuredAnswer.question.id,
        answer: answers[index],
      });
    });
    this.setState({ loading: true });

    // Reset the user's password
    this.apiService
      .resetPassword(apiAnswers, newPassword, username)
      .then(() => {
        this.setState({ loading: false });
        onResetSuccess();
      })
      .catch(error => {
        this.setState({ loading: false });
        onResetFailure(error);
      });
  };

  /**
   * Return the JSX of the component to render.
   */
  render() {
    const { configuredAnswers } = this.props;
    const { loading, newPasswordDisabled } = this.state;

    // Create a form group for every configured answer. This has to be dynamic because
    // the number of required answers will differ based on the deployment.
    const answerFormGroups = configuredAnswers.map((answer, index) => {
      const { question } = answer;
      const id = `answer${index}`;
      const value = this.state.answers[index];
      return (
        <FormGroup key={answer.id}>
          <Label for={id}>{question.question}</Label>
          <PasswordInput
            className="answer-input"
            data-id={index}
            disabled={loading}
            id={id}
            onChange={this.handleAnswerChange}
            placeholder="Enter your secret answer"
            required
            value={value}
          />
        </FormGroup>
      );
    });

    return (
      <Form onSubmit={this.handleResetSubmit}>
        {answerFormGroups}
        <FormGroup className="mt-5">
          <Label for="newPassword">New Password:</Label>
          <PasswordInput
            className="answer-input"
            disabled={loading || newPasswordDisabled}
            id="newPassword"
            name="newPassword"
            onChange={this.handleInputChange}
            placeholder="Enter your new password"
            required
          />
        </FormGroup>
        <FormGroup className="mt-2">
          <Label for="newPasswordRepeat">Repeat New Password:</Label>
          <PasswordInput
            className="answer-input"
            disabled={loading || newPasswordDisabled}
            id="newPasswordRepeat"
            name="newPasswordRepeat"
            onChange={this.handleInputChange}
            placeholder="Enter your new password again"
            required
          />
        </FormGroup>
        <Button className="mt-2" color="primary" disabled={loading || newPasswordDisabled}>
          Reset Password
        </Button>
      </Form>
    );
  }
}

export default VerifyAnswersForm;
