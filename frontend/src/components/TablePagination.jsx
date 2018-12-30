import React from 'react';
import { Link } from 'react-router-dom';
import { PropTypes } from 'prop-types';
import { Pagination, PaginationItem, PaginationLink } from 'reactstrap';

const TablePagination = (props) => {
  const baseURL = props.match.url.split('/').slice(0, -1).join('/');
  const currentPageNum = parseInt(props.match.params.page, 10);
  const pages = [];
  for (let pageNum = 1; pageNum <= props.pages; pageNum += 1) {
    const newPath = `${baseURL}/${pageNum}`;
    pages.push((
      <PaginationItem disabled={currentPageNum === pageNum} key={pageNum}>
        <PaginationLink tag={Link} to={newPath}>
          {pageNum}
        </PaginationLink>
      </PaginationItem>
    ));
  }

  return (
    <Pagination>
      {pages}
    </Pagination>
  );
};

TablePagination.propTypes = {
  pages: PropTypes.number.isRequired,
  match: PropTypes.object.isRequired,
};


export default TablePagination;
