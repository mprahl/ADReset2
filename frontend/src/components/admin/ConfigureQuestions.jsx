import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import { PropTypes } from 'prop-types';
import { Button, Container, Modal, ModalBody, ModalFooter, ModalHeader, Table } from 'reactstrap';

import './ConfigureQuestions.css';
import APIService from '../../utils/APIService';
import Spinner from '../common/Spinner';
import EditableColumn from '../common/EditableColumn';
import TablePagination from '../common/TablePagination';

class ConfigureQuestions extends Component {
  static propTypes = {
    displayToast: PropTypes.func.isRequired,
    match: PropTypes.object.isRequired,
  };

  constructor(props) {
    super(props);
    this.state = {
      questions: [],
      pages: 0,
      loading: true,
      modalOpen: false,
      newSecretQuestion: '',
      questionStates: {},
      // Used to keep track of the question to disable from the modal
      questionToBeDisabled: null,
    };
    // TODO: Pass in a configurable API URL
    this.apiService = new APIService();
    this.handleChange = this.handleChange.bind(this);
    this.addSecretQuestion = this.addSecretQuestion.bind(this);
    this.getQuestions = this.getQuestions.bind(this);
    this.handleEnabledButton = this.handleEnabledButton.bind(this);
    this.getQuestionIndex = this.getQuestionIndex.bind(this);
    this.handleNewQuestionEnter = this.handleNewQuestionEnter.bind(this);
    this.doneEditing = this.doneEditing.bind(this);
    this.questionUpdate = this.apiService.patchSecretQuestion.bind(this.apiService);
    this.handleModalClick = this.handleModalClick.bind(this);
    this.handleModalCancel = this.handleModalCancel.bind(this);
  }

  componentDidMount() {
    // Once the component mounts, query the API
    this.getQuestions();
  }

  componentDidUpdate(prevProps) {
    // If the page changed, then query the API again
    if (this.props.match.params.page !== prevProps.match.params.page) {
      this.getQuestions();
    }
  }

  componentWillUnmount() {
    // Cancel any outstanding GET API calls
    this.apiService.cancelGetSecretQuestions();
  }

  getQuestions() {
    this.setState({ loading: true });
    const page = parseInt(this.props.match.params.page, 10);
    this.apiService
      .getSecretQuestions(page)
      .then(data => {
        const questionStates = {};
        data.items.forEach(question => {
          questionStates[question.id] = { editing: false, btnDisabled: false };
        });
        this.setState({
          loading: false,
          pages: data.meta.pages,
          questions: data.items,
          questionStates,
        });
      })
      .catch(error => {
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

  setEnabled(questionID, enabled) {
    this.apiService
      .patchSecretQuestion(questionID, { enabled })
      .then(data => {
        const { questions } = this.state;
        questions[this.getQuestionIndex(questionID)].enabled = data.enabled;
        this.setState({ questions });
        this.props.displayToast(
          'success',
          `The question was ${data.enabled ? 'enabled' : 'disabled'}`,
        );
      })
      .catch(error => {
        this.props.displayToast('error', error.message);
      })
      .finally(() => {
        this.setState(prevState => {
          const { questionStates } = prevState;
          questionStates[questionID].editing = false;
          questionStates[questionID].btnDisabled = false;
          return { modalOpen: false, questionStates, questionToBeDisabled: null };
        });
      });
  }

  handleEnabledButton(event) {
    const btn = event.target;
    const questionID = parseInt(btn.parentElement.parentElement.attributes['data-id'].value, 10);
    this.setState(prevState => {
      const { questionStates } = prevState;
      questionStates[questionID].btnDisabled = true;
      return { questionStates };
    });

    const { enabled } = this.state.questions[this.getQuestionIndex(questionID)];
    if (enabled) {
      this.setState({ modalOpen: true, questionToBeDisabled: questionID });
    } else {
      this.setEnabled(questionID, true);
    }
  }

  doneEditing(id, key = null, value = null) {
    // If the value is null, then no changes were made
    if (value === null) {
      this.setState(prevState => {
        const { questionStates } = prevState;
        questionStates[id].editing = false;
        questionStates[id].btnDisabled = false;
        return { questionStates };
      });
      return;
    }

    this.setState(prevState => {
      const { questions, questionStates } = prevState;
      questions[this.getQuestionIndex(id)][key] = value;
      questionStates[id].editing = false;
      questionStates[id].btnDisabled = false;
      return { questions, questionStates };
    });
  }

  addSecretQuestion(event) {
    if (this.state.newSecretQuestion === '') {
      this.props.displayToast(
        'error',
        'You must enter a value before trying to add a secret question',
      );
      return;
    }

    const addQuestionInput = event.target.parentElement.parentElement.querySelector(
      'input.add-question-input',
    );
    addQuestionInput.disabled = true;
    this.apiService
      .addSecretQuestion(this.state.newSecretQuestion)
      .then(() => {
        this.setState({ newSecretQuestion: '' });
        this.getQuestions();
        addQuestionInput.disabled = false;
      })
      .catch(error => {
        this.props.displayToast('error', error.message);
        addQuestionInput.disabled = false;
      });
  }

  // eslint-disable-next-line class-methods-use-this
  handleNewQuestionEnter(event) {
    if (event.keyCode === 13) {
      const addBtn = event.target.parentElement.parentElement.querySelector(
        'button.add-question-btn',
      );
      addBtn.click();
    }
  }

  handleChange(event) {
    this.setState({ [event.target.name]: event.target.value });
  }

  handleModalClick(event) {
    const btn = event.target;
    btn.disabled = true;
    const { questionToBeDisabled } = this.state;
    this.setEnabled(questionToBeDisabled, false);
  }

  handleModalCancel() {
    this.setState(prevState => {
      const { questionStates, questionToBeDisabled } = prevState;
      questionStates[questionToBeDisabled].btnDisabled = false;
      return { modalOpen: false, questionStates };
    });
  }

  render() {
    if (this.state.loading === true) {
      return <Spinner />;
    }

    const questions = this.state.questions.map(v => (
      <tr key={v.id} data-id={v.id}>
        {this.state.questionStates[v.id].editing ? (
          <EditableColumn
            displayToast={this.props.displayToast}
            id={v.id}
            column="question"
            value={v.question}
            update={this.questionUpdate}
            done={this.doneEditing}
          />
        ) : (
          <td>
            <Button
              onClick={() => {
                this.setState(prevState => {
                  const { questionStates } = prevState;
                  questionStates[v.id].editing = true;
                  questionStates[v.id].btnDisabled = true;
                  return { questionStates };
                });
              }}
              color="link"
            >
              {v.question}
            </Button>
          </td>
        )}
        <td>
          <Button
            onClick={this.handleEnabledButton}
            disabled={this.state.questionStates[v.id].btnDisabled}
            color="link"
          >
            {v.enabled ? 'Disable' : 'Enable'}
          </Button>
        </td>
      </tr>
    ));

    questions.push(
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
          <Button onClick={this.addSecretQuestion} className="add-question-btn" color="link">
            Add
          </Button>
        </td>
      </tr>,
    );

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
          <tbody>{questions}</tbody>
        </Table>
        <TablePagination page={this.state.page} pages={this.state.pages} />
        {/* The modal that is triggered when the admin tries to disable a question */}
        <Modal isOpen={this.state.modalOpen} toggle={this.handleModalCancel}>
          <ModalHeader toggle={this.handleModalCancel}>Disable Question</ModalHeader>
          <ModalBody>
            By disabling this question, users will not be able to select this question when
            configuring their secret questions. Users that are currently using this question
            will not be affected.
          </ModalBody>
          <ModalFooter>
            <Button color="primary" onClick={this.handleModalClick}>
              Disable it
            </Button>
            <Button color="secondary" onClick={this.handleModalCancel}>
              Cancel
            </Button>
          </ModalFooter>
        </Modal>
      </Container>
    );
  }
}

export default withRouter(ConfigureQuestions);
