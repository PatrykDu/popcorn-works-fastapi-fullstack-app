document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('calendar');

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: function (fetchInfo, successCallback, failureCallback) {
            fetch('/your-endpoint-url')
                .then(function (response) {
                    return response.json();
                })
                .then(function (jsonData) {
                    var events = jsonData.map(function (item) {
                        return {
                            id: item.repair_id,
                            start: item.start_date,
                            end: item.end_date
                        };
                    });
                    successCallback(events);
                })
                .catch(function () {
                    failureCallback();
                });
        }
    });

    calendar.render();
});
