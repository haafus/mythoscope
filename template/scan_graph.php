<?php
// scan_graph.php
header('Content-Type: application/json; charset=utf-8');

// Пробуем найти папку graphs в разных возможных местах
$possiblePaths = [
    __DIR__ . '/../graphs/',           // graphs на уровень выше template
    __DIR__ . '/graphs/',               // graphs в той же папке
    dirname(__DIR__) . '/graphs/',      // альтернативный способ
    __DIR__ . '/../../graphs/'          // на два уровня выше
];

$dir = null;
foreach ($possiblePaths as $path) {
    if (is_dir($path)) {
        $dir = $path;
        break;
    }
}

// Если папка не найдена, создаем её
if (!$dir) {
    $dir = __DIR__ . '/../graphs/';
    if (!is_dir($dir)) {
        mkdir($dir, 0777, true);
    }
}

$allowed = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'html'];
$files = [];

if (is_dir($dir)) {
    $found = array_diff(scandir($dir), array('..', '.'));
    foreach ($found as $file) {
        $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
        if (in_array($ext, $allowed)) {
            $files[] = $file;
        }
    }
}

sort($files);
echo json_encode($files);
?>