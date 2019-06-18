'use strict';

/**
 * @param  {[type]} txid Transaction id
 * @param  {[type]} url endpoint to point at
 * Lähettää onnistuneen oston tiedot
 */
function articlePaid(txid, url) {
    var params = {'url': window.location.href, 'txid': txid};
    var ajaxRequest = $.ajax({
        async: true,
        url: url,
        type: 'POST',
        dataType: 'text',
        contentType: 'application/json; charset=utf-8',
        data: JSON.stringify(params),
    });
    ajaxRequest.done(paidSuccess);
    ajaxRequest.fail(ajaxError);
};

/**
 * Tulostaa ajaxin kutsussa taphatuneet virheet
 * @param  {[type]} xhr    [description]
 * @param  {[type]} status Virhe
 * @param  {[type]} error  Status
 */
function ajaxError(xhr, status, error) {
    console.log( 'Error: ' + error );
    console.log( 'Status: ' + status );
    console.log( xhr );
}

/**
 * Callback for success
 * @param  {[type]} msg [description]
 */
function paidSuccess(msg) {
    console.log(msg);
    console.log('Success');
    location.reload();
}


/**
 * Callback to execute on success
 * @param  {[type]} txid Transaction id
 */
function singlePayCallback(txid) {
    console.log('Success. Transaction ID:', txid);
    articlePaid(txid, '/api/articlepaid');
};


/**
 * Callback to execute on success
 * @param  {[type]} txid Transaction id
 */
function monthlyPayCallback(txid) {
    console.log('Success. Transaction ID:', txid);
    articlePaid(txid, '/api/monthpaid');
};


window.onload = function() {
    console.log('Window loaded');
};
