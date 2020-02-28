<?php
$res = file_get_contents("https://planner.ganttic.com/api/v1/tasks?timeMin=2019-01-01&timeMax=2020-01-01&token=[YOUR TOKEN HERE]");

$json = json_decode($res);
$tasks = $json->items;

foreach($tasks as $task) {
	echo $task->name;
	echo "<br>";
}
?>