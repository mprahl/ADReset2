import React, { Component } from 'react';
import { PropTypes } from 'prop-types';
import { FormGroup, Input, Label } from 'reactstrap';

import PasswordInput from '../common/PasswordInput';
import './SetAnswersFormGroup.css';

/**
 * Creates a form group consisting of a questions select input and answer text input.
 *
 * @class SetAnswersFormGroup
 * @extends {Component}
 */
class SetAnswersFormGroup extends Component {
  static propTypes = {
    configured: PropTypes.bool.isRequired,
    loading: PropTypes.bool,
    minLength: PropTypes.number.isRequired,
    questions: PropTypes.array.isRequired,
    questionNumber: PropTypes.number.isRequired,
    selectValue: PropTypes.number.isRequired,
    setSelectedAnswer: PropTypes.func.isRequired,
    setSelectedQuestion: PropTypes.func.isRequired,
  };

  static defaultProps = {
    loading: false,
  };

  /**
   * Handle input changes by calling the setSelectedQuestion prop.
   *
   * @param {*} event The event that triggered this handler.
   */
  handleInput = event => {
    const input = event.target;
    const index = parseInt(input.attributes['data-id'].value, 10);
    this.props.setSelectedAnswer(index, input.value.trim());
  };

  /**
   * Handle select changes by calling the setSelectedQuestion prop.
   *
   * @param {*} event The event that triggered this handler.
   */
  handleSelect = event => {
    const select = event.target;
    const index = parseInt(select.attributes['data-id'].value, 10);
    const selectedQuestionID = parseInt(select.value, 10);
    this.props.setSelectedQuestion(index, selectedQuestionID);
  };

  /**
   * Toggles the visibility of the answer input field.
   */
  toggleVisibility = () => {
    this.setState(oldState => ({ visible: !oldState.visible }));
  };

  /**
   * Return the JSX of the component to render.
   */
  render() {
    const { configured, loading, minLength, questions, questionNumber, selectValue } = this.props;

    // Create an option for each possible question
    const questionOptions = questions.map(question => (
      <option key={question.id} value={question.id}>
        {question.question}
      </option>
    ));

    // The question indexes start at 0, but the user should see 1 instead
    const displayQuestionNumber = questionNumber + 1;
    return (
      <FormGroup key={displayQuestionNumber} className="mb-4">
        <Label for={`question${displayQuestionNumber}`} className="question-label">
          {`Question ${displayQuestionNumber}:`}
        </Label>
        <Input
          className="question-input"
          disabled={configured || loading}
          data-id={questionNumber}
          id={`question${displayQuestionNumber}`}
          name={`select${displayQuestionNumber}`}
          onChange={this.handleSelect}
          required={!configured}
          type="select"
          value={selectValue}
        >
          {questionOptions}
        </Input>
        <PasswordInput
          className="mt-2 question-input"
          data-id={questionNumber}
          disabled={configured || loading}
          minLength={minLength}
          name={`answer${displayQuestionNumber}`}
          onChange={this.handleInput}
          placeholder={configured ? 'Your answer is set' : 'Please enter an answer'}
          required={!configured}
        />
      </FormGroup>
    );
  }
}

export default SetAnswersFormGroup;
