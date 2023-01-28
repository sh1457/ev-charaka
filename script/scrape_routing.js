var data = {}

let routing = document.querySelector("div#routing")

data["trip_name"] = routing.querySelector("div#trip-name div.mobileTitle").innerText

let path = routing.querySelector("div#path")

var waypoints = []
path.querySelector("div.waypoints").querySelectorAll("div.waypoint").forEach(
    (wp) => {
        var inner_data = {}

        inner_data["icon"] = wp.querySelector("div.sprite div").className
        inner_data["display"] = wp.querySelector("div.mobileWaypoint div.display").innerText
        inner_data["address"] = wp.querySelector("div.mobileWaypoint div.address").innerText
        inner_data["distance"] = wp.querySelector("div.leg-span span.distance").innerText
        inner_data["duration"] = wp.querySelector("div.leg-span span.duration").innerText

        waypoints.push(inner_data)
    }
)

data["waypoints"] = waypoints
data["maps_link"] = document.querySelector("div#directions div.headlink a").getAttribute("href")

console.log(JSON.stringify(data))