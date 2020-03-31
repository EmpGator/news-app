function sendAnalytics(a) {
    console.log('sending stuff');
    var img = new Image;
    img.src = '/a?url=' + a.url + '&t=' + a.title + '&ref=' + a.ref + '&time=' + a.time + '&dur=' +
      a.dur + '&lat=' + a.lat + '&lon=' + a.lon + '&dev=' + a.dev;
}

function getAnalytics(lat, lon, dur, time) {
    let url = encodeURIComponent(document.location.href);
    let title = encodeURIComponent(document.title);
    let ref = encodeURIComponent(document.referrer);
    let md = new MobileDetect(navigator.userAgent);
    let dev = 'PC';
    if (md.phone()) dev = md.phone();
    if (md.tablet()) dev = md.tablet();

    return {
        'url': url,
        'title': title,
        'ref': ref,
        'lat': lat,
        'lon': lon,
        'dur': dur,
        'time': time,
        'dev': dev
    }
}


var lat = 0;
var lon = 0;
var time = new Date().getTime();

TimeMe.initialize({
    currentPageName: "dashboard", // current page
    idleTimeoutInSeconds: 180 // seconds
});


navigator.geolocation.getCurrentPosition(pos => {
    lat = pos.coords.latitude;
    lon = pos.coords.longitude;
});


window.onbeforeunload = function(e) {
    let dur = TimeMe.getTimeOnCurrentPageInSeconds();
    sendAnalytics(getAnalytics(lat, lon, dur,time));
};

