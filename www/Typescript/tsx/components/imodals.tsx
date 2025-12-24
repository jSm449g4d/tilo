import React from 'react';

export const HIModal = (_title = "", _text = "") => {
    $('#helpInfoModal').modal('show');
    $('#helpInfoModalTitle').text(String(_title))
    $('#helpInfoModalText').text(String(_text))
}

export const CIModal = (_title: String = "", _text: string = "") => {
    $('#cautionInfoModal').modal('show');
    $('#cautionInfoModalTitle').text(String(_title))
    $('#cautionInfoModalText').text(String(_text))
}

export const IModalsRender = () => {
    const helpInfoModal = () => {
        return (
            <div className="modal fade" id="helpInfoModal" aria-labelledby="exampleModalLabel" aria-hidden="true">
                <div className="modal-dialog">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h4 className="modal-title">
                                <i className="fa-solid fa-circle-info text-info mx-1" />
                            </h4>
                            <h4 className="modal-title" id="helpInfoModalTitle">
                                help
                            </h4>
                        </div>
                        <div className="modal-body" id="helpInfoModalText" style={{ "wordBreak": "break-all" }}></div>
                        <div className="modal-footer">
                            <button type="button" className="btn btn-outline-secondary" data-bs-dismiss="modal">
                                <i className="fa-solid fa-otter mx-1" style={{ pointerEvents: "none" }} />Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        )
    }
    const cautionInfoModal = () => {
        return (
            <div className="modal fade" id="cautionInfoModal" aria-labelledby="exampleModalLabel" aria-hidden="true">
                <div className="modal-dialog">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h4 className="modal-title">
                                <i className="fa-solid fa-circle-exclamation text-warning mx-1" />
                            </h4>
                            <h4 className="modal-title" id="cautionInfoModalTitle">
                                caution
                            </h4>
                        </div>
                        <div className="modal-body" id="cautionInfoModalText" style={{ "wordBreak": "break-all" }}></div>
                        <div className="modal-footer">
                            <button type="button" className="btn btn-outline-secondary" data-bs-dismiss="modal">
                                <i className="fa-solid fa-otter mx-1" style={{ pointerEvents: "none" }} />Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        )
    }
    return (
        <div>
            {helpInfoModal()}
            {cautionInfoModal()}
        </div>
    )
}
