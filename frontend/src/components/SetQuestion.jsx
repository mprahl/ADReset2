import React, { Component } from 'react';
import { PropTypes } from 'prop-types';
import { Container, Table, Button } from 'reactstrap';

import './SetQuestion.css';
import APIService from './APIService';
import Spinner from './Spinner';
import EditableColumn from './EditableColumn';


class SetQuestion extends Component {
  static propTypes = {
    displayToast: PropTypes.func.isRequired,
  }

  constructor(props) {
    super(props);
    this.state = {
      questions: [],
      loading: true,
      newSecretQuestion: '',
      questionEditID: null,
    };
    // TODO: Pass in a configurable API URL
    this.apiService = new APIService();
    this.handleChange = this.handleChange.bind(this);
    this.addSecretQuestion = this.addSecretQuestion.bind(this);
    this.getQuestions = this.getQuestions.bind(this);
    this.setEnabled = this.setEnabled.bind(this);
    this.getQuestionIndex = this.getQuestionIndex.bind(this);
    this.handleNewQuestionEnter = this.handleNewQuestionEnter.bind(this);
    this.doneEditing = this.doneEditing.bind(this);
    this.questionUpdate = this.apiService.patchSecretQuestion.bind(this.apiService);
  }

  componentDidMount() {
    this.getQuestions();
  }

  getQuestions() {
    // TODO: Add pagination support
    this.setState({ loading: true });
    this.apiService.getSecretQuestions()
      .then((data) => {
        this.setState({ loading: false, questions: data.items });
      })
      .catch((error) => {
        this.props.displayToast('error', error.message);
      });
  }

  getQuestionIndex(questionID) {
    for (let i = 0; i < this.state.questions.length; i += 1) {
      if (this.state.questions[i].id === questionID) {
        return i;
      }
    }
    throw new Error(`The question with the ID ${questionID} is not stored in the state`);
  }

  setEnabled(event) {
    const btn = event.target;
    btn.disabled = true;
    const questionID = parseInt(event.target.parentElement.parentElement.attributes['data-id'].value, 10);

    const enabled = !this.state.questions[this.getQuestionIndex(questionID)].enabled;

    this.apiService.patchSecretQuestion(questionID, { enabled })
      .then((data) => {
        const { questions } = this.state;
        questions[this.getQuestionIndex(questionID)].enabled = data.enabled;
        this.setState({ questions });
        this.props.displayToast('success', `The question was ${data.enabled ? 'enabled' : 'disabled'}`);
        btn.disabled = false;
      })
      .catch((error) => {
        this.props.displayToast('error', error.message);
        btn.disabled = false;
      });
  }

  doneEditing(id = null, key = null, value = null) {
    // If the value is null, then no changes were made
    if (value === null) {
      this.setState({ questionEditID: null });
      return;
    }

    const { questions } = this.state;
    questions[this.getQuestionIndex(id)][key] = value;
    this.setState({ questions, questionEditID: null });
  }

  addSecretQuestion(event) {
    if (this.state.newSecretQuestion === '') {
      this.props.displayToast('error', 'You must enter a value before trying to add a secret question');
      return;
    }

    const addQuestionInput = event.target.parentElement.parentElement.querySelector('input.add-question-input');
    addQuestionInput.disabled = true;
    this.apiService.addSecretQuestion(this.state.newSecretQuestion)
      .then(() => {
        this.setState({ newSecretQuestion: '' });
        this.getQuestions();
        addQuestionInput.disabled = false;
      })
      .catch((error) => {
        this.props.displayToast('error', error.message);
        addQuestionInput.disabled = false;
      });
  }

  // eslint-disable-next-line class-methods-use-this
  handleNewQuestionEnter(event) {
    if (event.keyCode === 13) {
      const addBtn = event.target.parentElement.parentElement.querySelector('button.add-question-btn');
      addBtn.click();
    }
  }

  handleChange(event) {
    this.setState({ [event.target.name]: event.target.value });
  }

  render() {
    if (this.state.loading === true) {
      return (
        <Spinner />
      );
    }

    const questions = this.state.questions.map(v => (
      <tr key={v.id} data-id={v.id}>
        {
          this.state.questionEditID === v.id
            ? (
              <EditableColumn
                displayToast={this.props.displayToast}
                id={v.id}
                column="question"
                value={v.question}
                update={this.questionUpdate}
                done={this.doneEditing}
              />
            )
            : (
              <td>
                <Button
                  onClick={() => {
                    this.setState({ questionEditID: v.id });
                  }}
                  color="link"
                >
                  {v.question}
                </Button>
              </td>
            )
        }
        <td>
          <Button onClick={this.setEnabled} color="link">
            {v.enabled ? 'Disable' : 'Enable'}
          </Button>
        </td>
      </tr>
    ));

    questions.push((
      <tr key="add">
        <td>
          <input
            onChange={this.handleChange}
            onKeyUp={this.handleNewQuestionEnter}
            value={this.state.newSecretQuestion}
            name="newSecretQuestion"
            className="form-control add-question-input"
            placeholder="Add a secret question"
          />
        </td>
        <td>
          <Button onClick={this.addSecretQuestion} className="add-question-btn" color="link">Add</Button>
        </td>
      </tr>
    ));

    return (
      <Container>
        <h2 className="text-center mb-5">Manage Secret Questions</h2>
        <Table hover bordered responsive className="secret-questions-table">
          <thead className="thead-blue">
            <tr>
              <th>Secret Question</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {questions}
          </tbody>
        </Table>
      </Container>
    );
  }
}


export default SetQuestion;
