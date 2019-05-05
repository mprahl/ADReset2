import { PropTypes } from 'prop-types';
import React, { Component } from 'react';
import { Button, Form, FormGroup, Input, Label } from 'reactstrap';
import { withRouter } from 'react-router-dom';

import './VerifyAnswers.css';

class UsernameForm extends Component {
  static propTypes = {
    baseURL: PropTypes.string.isRequired,
    disabled: PropTypes.bool,
    history: PropTypes.object.isRequired,
    match: PropTypes.object.isRequired,
  };

  static defaultProps = {
    disabled: false,
  };

  constructor(props) {
    super(props);
    // In case the input is disabled, there should still be the value from the route shown
    const { username } = this.props.match.params;
    this.state = { username: username || '' };
  }

  /**
   * Handles when the username text box changes.
   *
   * @param {*} e The event that triggered this method.
   */
  handleInputChange = e => {
    const { value } = e.target;
    this.setState({ username: value });
  };

  /**
   * Handles when the username form is submitted.
   *
   * @param {*} e The event that triggered this method.
   */
  handleUsernameSubmit = e => {
    e.preventDefault();
    const { username } = this.state;
    const { baseURL, history } = this.props;
    if (username) {
      // The VerifyAnswers component reads the username from the route
      history.push(`${baseURL}${username}`);
    }
  };

  /**
   * Return the JSX of the component to render.
   */
  render() {
    const { disabled } = this.props;
    const { username } = this.state;
    return (
      <Form onSubmit={this.handleUsernameSubmit} className="mb-4">
        <FormGroup>
          <Label for="username">Username:</Label>
          <Input
            className="answer-input"
            disabled={disabled}
            id="username"
            onChange={this.handleInputChange}
            placeholder="Enter your username to load your questions"
            required
            value={username}
          />
        </FormGroup>
        <Button color="primary" disabled={disabled}>
          Show Questions
        </Button>
      </Form>
    );
  }
}

export default withRouter(UsernameForm);
